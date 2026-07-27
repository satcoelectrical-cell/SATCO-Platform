from __future__ import annotations

from datetime import datetime
from datetime import timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.enums import ContextAuthority
from app.enums import ContextConfidentiality
from app.enums import ContextKind
from app.enums import ContextLifecycle
from app.enums import ContextScope
from app.enums import ContextSourceKind
from app.enums import ContextSubjectKind
from app.enums import Discipline
from app.enums import WorkspaceStatus
from app.exceptions.engineering_context import ContextForbidden
from app.exceptions.engineering_context import ContextLifecycleConflict
from app.exceptions.engineering_context import ContextNotFound
from app.exceptions.engineering_context import ContextVersionConflict
from app.exceptions.engineering_context import InvalidContext
from app.exceptions.engineering_context import InvalidContextResponsibility
from app.models.engineering_context import EngineeringContext
from app.models.engineering_context import EngineeringContextSourceReference
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.project import Project
from app.models.user import User
from app.repositories.engineering_context_repository import (
    EngineeringContextRepository,
)
from app.services.audit_service import create_audit_log


FACT_FIELDS = {"statement", "uncertainty"}
VALUE_FIELDS = {
    "numeric_value",
    "unit",
    "quantity_type",
    "tolerance_min",
    "tolerance_max",
    "range_min",
    "range_max",
    "basis",
    "condition_type",
    "condition",
    "uncertainty",
}
ASSUMPTION_FIELDS = {
    "statement",
    "reason",
    "consequence",
    "confirmation_condition",
}


class EngineeringContextService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = EngineeringContextRepository(db)

    def create_context(
        self,
        *,
        project_id: int,
        workspace_id: int | None,
        kind: ContextKind | str,
        authority: ContextAuthority | str,
        owner_id: int,
        steward_id: int,
        current_user: User,
        payload: dict | None = None,
        subjects: list[dict] | None = None,
        sources: list[dict] | None = None,
        purpose: str | None = None,
        context_key: str | None = None,
    ) -> dict:
        kind = self._enum(ContextKind, kind, "Context kind")
        authority = self._enum(
            ContextAuthority,
            authority,
            "Context authority",
        )
        project = self._require_project(project_id)
        workspace = self._validate_scope(
            project_id=project_id,
            workspace_id=workspace_id,
        )
        self._require_contribution_access(
            project=project,
            workspace=workspace,
            current_user=current_user,
        )
        owner = self._require_active_user(owner_id)
        steward = self._require_active_user(steward_id)
        self._validate_initial_authority(
            kind=kind,
            authority=authority,
            steward=steward,
            current_user=current_user,
            sources=sources or [],
        )
        payload_values = self._validate_payload(
            kind,
            payload,
            partial=False,
        )
        subject_values = self._validate_subjects(
            project=project,
            workspace=workspace,
            subjects=subjects or [],
        )
        source_values = self._validate_sources(
            sources or [],
            current_user=current_user,
        )
        if (
            kind == ContextKind.SUBJECT_REFERENCE
            and not subject_values
        ):
            raise InvalidContext(
                "Subject Reference Context requires a subject"
            )
        if (
            kind == ContextKind.SOURCE_EVIDENCE_REFERENCE
            and not source_values
        ):
            raise InvalidContext(
                "Source and Evidence Reference requires a source"
            )

        scope = (
            ContextScope.WORKSPACE
            if workspace is not None
            else ContextScope.PROJECT
        )
        values = {
            "context_key": context_key or str(uuid4()),
            "kind": kind.value,
            "scope": scope.value,
            "project_id": project.id,
            "workspace_id": workspace.id if workspace else None,
            "owner_id": owner.id,
            "steward_id": steward.id,
            "created_by_id": current_user.id,
            "authority": authority.value,
            "lifecycle": ContextLifecycle.CURRENT.value,
            "purpose": self._normalize_optional(purpose),
            "version": 1,
        }
        try:
            context = self.repository.create(
                context_values=values,
                payload_values=payload_values,
                subject_values=subject_values,
                source_values=source_values,
            )
            self._audit_and_commit(
                current_user=current_user,
                action="engineering_context_created",
                context_id=context.id,
                details={
                    "project_id": project.id,
                    "workspace_id": values["workspace_id"],
                    "context_key": values["context_key"],
                    "kind": kind.value,
                    "owner_id": owner.id,
                    "steward_id": steward.id,
                    "authority": authority.value,
                    "lifecycle": ContextLifecycle.CURRENT.value,
                    "version": 1,
                },
            )
        except IntegrityError as exc:
            self.db.rollback()
            raise InvalidContext(
                "Context identity or relationship violates integrity"
            ) from exc
        return self.get(context.id, current_user)

    def get(self, context_id: int, current_user: User) -> dict:
        return self._response(
            self._get_visible(context_id, current_user)
        )

    def list_for_scope(
        self,
        *,
        project_id: int,
        workspace_id: int | None,
        current_user: User,
        page: int = 1,
        size: int = 100,
        include_withdrawn: bool = False,
    ) -> dict:
        if page < 1 or size < 1 or size > 100:
            raise InvalidContext("Invalid Context pagination")
        if not self._is_active_actor(current_user):
            raise ContextForbidden()
        project = self._require_project(project_id)
        workspace = self._validate_scope(
            project_id=project_id,
            workspace_id=workspace_id,
        )
        items, total = self.repository.list_for_scope(
            project_id=project_id,
            workspace_id=workspace_id,
            current_user=current_user,
            page=page,
            size=size,
            include_withdrawn=include_withdrawn,
        )
        return {
            "items": [self._response(item) for item in items],
            "total": total,
            "page": page,
            "size": size,
        }

    def update_payload(
        self,
        *,
        context_id: int,
        expected_version: int,
        values: dict,
        reason: str,
        current_user: User,
    ) -> dict:
        context = self._get_visible(context_id, current_user)
        self._require_current(context)
        self._require_edit_access(context, current_user)
        kind = ContextKind(context.kind)
        payload_values = self._validate_payload(
            kind,
            values,
            partial=True,
        )
        if not payload_values:
            raise InvalidContext("At least one Context value is required")
        reason = self._normalize_required(reason, "Update reason")
        before = self._snapshot(context)
        try:
            self._versioned_update(
                context=context,
                expected_version=expected_version,
                values={},
            )
            self.repository.update_payload(context, payload_values)
            after = {
                **before,
                "version": expected_version + 1,
                "payload": {
                    **before.get("payload", {}),
                    **self._serialized(payload_values),
                },
            }
            self._audit_and_commit(
                current_user=current_user,
                action="engineering_context_updated",
                context_id=context.id,
                details={
                    "project_id": context.project_id,
                    "workspace_id": context.workspace_id,
                    "reason": reason,
                    "before": before,
                    "after": after,
                    "version": expected_version + 1,
                },
            )
        except IntegrityError as exc:
            self.db.rollback()
            raise InvalidContext(
                "Context value violates integrity"
            ) from exc
        return self.get(context_id, current_user)

    def change_responsibility(
        self,
        *,
        context_id: int,
        expected_version: int,
        owner_id: int | None,
        steward_id: int | None,
        reason: str,
        current_user: User,
    ) -> dict:
        context = self._get_visible(context_id, current_user)
        self._require_current(context)
        self._require_governance_access(context, current_user)
        if owner_id is None and steward_id is None:
            raise InvalidContext(
                "Owner or steward change is required"
            )
        if owner_id is not None and steward_id is not None:
            raise InvalidContext(
                "Owner and steward changes require separate audited actions"
            )
        values: dict = {}
        if owner_id is not None:
            values["owner_id"] = self._require_active_user(owner_id).id
        if steward_id is not None:
            values["steward_id"] = self._require_active_user(
                steward_id
            ).id
        reason = self._normalize_required(
            reason,
            "Responsibility change reason",
        )
        before = self._snapshot(context)
        self._versioned_update(
            context=context,
            expected_version=expected_version,
            values=values,
        )
        action = (
            "engineering_context_owner_changed"
            if owner_id is not None
            else "engineering_context_steward_changed"
        )
        self._audit_and_commit(
            current_user=current_user,
            action=action,
            context_id=context.id,
            details={
                "project_id": context.project_id,
                "workspace_id": context.workspace_id,
                "reason": reason,
                "before": before,
                "after": {
                    **before,
                    **values,
                    "version": expected_version + 1,
                },
                "version": expected_version + 1,
            },
        )
        return self.get(context_id, current_user)

    def change_authority(
        self,
        *,
        context_id: int,
        expected_version: int,
        authority: ContextAuthority | str,
        reason: str,
        current_user: User,
    ) -> dict:
        context = self._get_visible(context_id, current_user)
        self._require_current(context)
        if current_user.id != context.steward_id:
            raise ContextForbidden()
        authority = self._enum(
            ContextAuthority,
            authority,
            "Context authority",
        )
        if authority == ContextAuthority.ENGINEER_VERIFIED_FACT:
            raise InvalidContext(
                "Engineer verification belongs to a later Human Review patch"
            )
        if context.kind == ContextKind.ASSUMPTION.value:
            if authority != ContextAuthority.ASSUMPTION:
                raise InvalidContext(
                    "Assumption cannot be promoted to fact"
                )
        elif authority == ContextAuthority.ASSUMPTION:
            raise InvalidContext(
                "Non-Assumption Context cannot use Assumption authority"
            )
        if (
            authority == ContextAuthority.AUTHORITATIVE_FACT
            and context.kind
            in {
                ContextKind.QUALIFIED_FACT.value,
                ContextKind.QUALIFIED_ENGINEERING_VALUE.value,
            }
            and not context.source_references
        ):
            raise InvalidContext(
                "Authoritative Context requires source evidence"
            )
        reason = self._normalize_required(
            reason,
            "Authority change reason",
        )
        before = self._snapshot(context)
        self._versioned_update(
            context=context,
            expected_version=expected_version,
            values={"authority": authority.value},
        )
        self._audit_and_commit(
            current_user=current_user,
            action="engineering_context_authority_changed",
            context_id=context.id,
            details={
                "project_id": context.project_id,
                "workspace_id": context.workspace_id,
                "reason": reason,
                "before": before,
                "after": {
                    **before,
                    "authority": authority.value,
                    "version": expected_version + 1,
                },
                "version": expected_version + 1,
            },
        )
        return self.get(context_id, current_user)

    def add_source(
        self,
        *,
        context_id: int,
        expected_version: int,
        source: dict,
        reason: str,
        current_user: User,
    ) -> dict:
        context = self._get_visible(context_id, current_user)
        self._require_current(context)
        self._require_edit_access(context, current_user)
        values = self._validate_sources(
            [source],
            current_user=current_user,
        )[0]
        reason = self._normalize_required(
            reason,
            "Source change reason",
        )
        before = self._snapshot(context)
        try:
            self._versioned_update(
                context=context,
                expected_version=expected_version,
                values={},
            )
            self.repository.add_source_reference(
                context_id=context.id,
                values=values,
            )
            self._audit_and_commit(
                current_user=current_user,
                action="engineering_context_source_linked",
                context_id=context.id,
                details={
                    "project_id": context.project_id,
                    "workspace_id": context.workspace_id,
                    "reason": reason,
                    "before": before,
                    "after_source": self._safe_source(values),
                    "version": expected_version + 1,
                },
            )
        except IntegrityError as exc:
            self.db.rollback()
            raise InvalidContext(
                "Source reference violates integrity"
            ) from exc
        return self.get(context_id, current_user)

    def remove_source(
        self,
        *,
        context_id: int,
        source_id: int,
        expected_version: int,
        reason: str,
        current_user: User,
    ) -> dict:
        context = self._get_visible(context_id, current_user)
        self._require_current(context)
        self._require_edit_access(context, current_user)
        source = self.repository.get_source_reference(
            context_id=context.id,
            source_id=source_id,
        )
        if source is None:
            raise ContextNotFound(context_id)
        if (
            context.authority
            == ContextAuthority.AUTHORITATIVE_FACT.value
            and context.kind
            in {
                ContextKind.QUALIFIED_FACT.value,
                ContextKind.QUALIFIED_ENGINEERING_VALUE.value,
            }
            and len(context.source_references) == 1
        ):
            raise InvalidContext(
                "Authoritative Context must retain source evidence"
            )
        reason = self._normalize_required(
            reason,
            "Source change reason",
        )
        safe_source = self._source_response(source)
        self._versioned_update(
            context=context,
            expected_version=expected_version,
            values={},
        )
        self.repository.remove_source_reference(source)
        self._audit_and_commit(
            current_user=current_user,
            action="engineering_context_source_unlinked",
            context_id=context.id,
            details={
                "project_id": context.project_id,
                "workspace_id": context.workspace_id,
                "reason": reason,
                "source": safe_source,
                "version": expected_version + 1,
            },
        )
        return self.get(context_id, current_user)

    def withdraw(
        self,
        *,
        context_id: int,
        expected_version: int,
        reason: str,
        current_user: User,
    ) -> dict:
        return self._change_lifecycle(
            context_id=context_id,
            expected_version=expected_version,
            target=ContextLifecycle.WITHDRAWN,
            reason=reason,
            current_user=current_user,
        )

    def restore(
        self,
        *,
        context_id: int,
        expected_version: int,
        reason: str,
        current_user: User,
    ) -> dict:
        return self._change_lifecycle(
            context_id=context_id,
            expected_version=expected_version,
            target=ContextLifecycle.CURRENT,
            reason=reason,
            current_user=current_user,
        )

    def _change_lifecycle(
        self,
        *,
        context_id: int,
        expected_version: int,
        target: ContextLifecycle,
        reason: str,
        current_user: User,
    ) -> dict:
        context = self._get_visible(context_id, current_user)
        self._require_governance_access(context, current_user)
        current = ContextLifecycle(context.lifecycle)
        if current == target:
            raise ContextLifecycleConflict(
                current.value,
                target.value,
            )
        reason = self._normalize_required(
            reason,
            "Lifecycle change reason",
        )
        before = self._snapshot(context)
        now = datetime.now(timezone.utc)
        values = (
            {
                "lifecycle": ContextLifecycle.WITHDRAWN.value,
                "withdrawal_reason": reason,
                "withdrawn_at": now,
            }
            if target == ContextLifecycle.WITHDRAWN
            else {
                "lifecycle": ContextLifecycle.CURRENT.value,
                "withdrawal_reason": None,
                "withdrawn_at": None,
            }
        )
        self._versioned_update(
            context=context,
            expected_version=expected_version,
            values=values,
        )
        self._audit_and_commit(
            current_user=current_user,
            action=(
                "engineering_context_withdrawn"
                if target == ContextLifecycle.WITHDRAWN
                else "engineering_context_restored"
            ),
            context_id=context.id,
            details={
                "project_id": context.project_id,
                "workspace_id": context.workspace_id,
                "reason": reason,
                "before": before,
                "after": {
                    **before,
                    "lifecycle": target.value,
                    "version": expected_version + 1,
                },
                "version": expected_version + 1,
            },
        )
        return self.get(context_id, current_user)

    def _versioned_update(
        self,
        *,
        context: EngineeringContext,
        expected_version: int,
        values: dict,
    ) -> None:
        if expected_version < 1:
            raise InvalidContext("Expected version must be positive")
        if not self.repository.update_versioned(
            context_id=context.id,
            expected_version=expected_version,
            values=values,
        ):
            self.db.rollback()
            raise ContextVersionConflict()

    def _get_visible(
        self,
        context_id: int,
        current_user: User,
    ) -> EngineeringContext:
        if not self._is_active_actor(current_user):
            raise ContextNotFound(context_id)
        context = self.repository.get_visible_by_id(
            context_id,
            current_user,
        )
        if context is None:
            raise ContextNotFound(context_id)
        return context

    def _require_project(self, project_id: int) -> Project:
        project = self.repository.get_project(project_id)
        if project is None:
            raise InvalidContext("Project does not exist")
        return project

    def _validate_scope(
        self,
        *,
        project_id: int,
        workspace_id: int | None,
    ) -> EngineeringWorkspace | None:
        if workspace_id is None:
            return None
        workspace = self.repository.get_workspace(workspace_id)
        if workspace is None or workspace.project_id != project_id:
            raise InvalidContext(
                "Workspace must belong to the governing Project"
            )
        if workspace.status == WorkspaceStatus.ARCHIVED.value:
            raise InvalidContext(
                "Archived Workspace cannot receive current Context"
            )
        return workspace

    def _require_active_user(self, user_id: int) -> User:
        user = self.repository.get_user(user_id)
        if (
            user is None
            or not user.is_active
            or user.role not in {"admin", "engineer"}
        ):
            raise InvalidContextResponsibility()
        return user

    def _validate_initial_authority(
        self,
        *,
        kind: ContextKind,
        authority: ContextAuthority,
        steward: User,
        current_user: User,
        sources: list[dict],
    ) -> None:
        if authority == ContextAuthority.ENGINEER_VERIFIED_FACT:
            raise InvalidContext(
                "Engineer verification belongs to a later Human Review patch"
            )
        if kind == ContextKind.ASSUMPTION:
            if authority != ContextAuthority.ASSUMPTION:
                raise InvalidContext(
                    "Assumption must retain Assumption authority"
                )
            return
        if authority == ContextAuthority.ASSUMPTION:
            raise InvalidContext(
                "Only Assumption Context may use Assumption authority"
            )
        if (
            kind
            in {
                ContextKind.QUALIFIED_FACT,
                ContextKind.QUALIFIED_ENGINEERING_VALUE,
            }
            and not sources
        ):
            raise InvalidContext(
                "Authoritative Context requires source evidence"
            )
        if (
            kind
            in {
                ContextKind.QUALIFIED_FACT,
                ContextKind.QUALIFIED_ENGINEERING_VALUE,
            }
            and steward.id != current_user.id
        ):
            raise ContextForbidden()

    def _validate_payload(
        self,
        kind: ContextKind,
        payload: dict | None,
        *,
        partial: bool,
    ) -> dict | None:
        required: set[str]
        allowed: set[str]
        if kind == ContextKind.QUALIFIED_FACT:
            required = {"statement"}
            allowed = FACT_FIELDS
        elif kind == ContextKind.QUALIFIED_ENGINEERING_VALUE:
            required = {
                "numeric_value",
                "unit",
                "quantity_type",
                "basis",
                "condition_type",
                "condition",
            }
            allowed = VALUE_FIELDS
        elif kind == ContextKind.ASSUMPTION:
            required = ASSUMPTION_FIELDS
            allowed = ASSUMPTION_FIELDS
        else:
            if payload:
                raise InvalidContext(
                    "This Context kind does not accept value payload"
                )
            return None

        if payload is None:
            raise InvalidContext("Context value payload is required")
        extra = set(payload) - allowed
        missing = required - set(payload)
        if extra:
            raise InvalidContext(
                "Unsupported Context value fields: "
                + ", ".join(sorted(extra))
            )
        if missing and not partial:
            raise InvalidContext(
                "Missing Context value fields: "
                + ", ".join(sorted(missing))
            )
        normalized = dict(payload)
        for field in allowed & set(normalized):
            value = normalized[field]
            if field in {
                "numeric_value",
                "tolerance_min",
                "tolerance_max",
                "range_min",
                "range_max",
            }:
                if value is not None:
                    try:
                        normalized[field] = Decimal(str(value))
                    except Exception as exc:
                        raise InvalidContext(
                            f"{field} must be numeric"
                        ) from exc
            elif value is not None:
                normalized[field] = self._normalize_required(
                    value,
                    field,
                )
        self._validate_ranges(normalized)
        return normalized

    @staticmethod
    def _validate_ranges(values: dict) -> None:
        for minimum, maximum in (
            ("tolerance_min", "tolerance_max"),
            ("range_min", "range_max"),
        ):
            low = values.get(minimum)
            high = values.get(maximum)
            if low is not None and high is not None and low > high:
                raise InvalidContext(
                    f"{minimum} must not exceed {maximum}"
                )

    def _validate_subjects(
        self,
        *,
        project: Project,
        workspace: EngineeringWorkspace | None,
        subjects: list[dict],
    ) -> list[dict]:
        normalized: list[dict] = []
        identities: set[tuple] = set()
        for subject in subjects:
            try:
                kind = self._enum(
                    ContextSubjectKind,
                    subject["subject_kind"],
                    "Context subject kind",
                )
            except KeyError as exc:
                raise InvalidContext(
                    "Context subject kind is required"
                ) from exc
            values = {
                "subject_kind": kind.value,
                "subject_project_id": None,
                "subject_workspace_id": None,
                "discipline": None,
            }
            if kind == ContextSubjectKind.PROJECT:
                subject_id = subject.get("project_id")
                if subject_id != project.id:
                    raise InvalidContext(
                        "Project subject must match Context Project"
                    )
                values["subject_project_id"] = subject_id
            elif kind == ContextSubjectKind.WORKSPACE:
                subject_id = subject.get("workspace_id")
                referenced = self.repository.get_workspace(subject_id)
                if (
                    referenced is None
                    or referenced.project_id != project.id
                    or workspace is None
                    or referenced.id != workspace.id
                ):
                    raise InvalidContext(
                        "Workspace subject must match Context scope"
                    )
                values["subject_workspace_id"] = referenced.id
            else:
                discipline = self._enum(
                    Discipline,
                    subject.get("discipline"),
                    "Discipline subject",
                )
                if (
                    workspace is not None
                    and workspace.discipline != discipline.value
                ):
                    raise InvalidContext(
                        "Discipline subject must match Workspace"
                    )
                values["discipline"] = discipline.value
            identity = tuple(values.values())
            if identity in identities:
                raise InvalidContext(
                    "Duplicate Context subject reference"
                )
            identities.add(identity)
            normalized.append(values)
        return normalized

    def _validate_sources(
        self,
        sources: list[dict],
        *,
        current_user: User,
    ) -> list[dict]:
        normalized: list[dict] = []
        identities: set[tuple[str, str, str]] = set()
        for source in sources:
            try:
                kind = self._enum(
                    ContextSourceKind,
                    source["source_kind"],
                    "Context source kind",
                )
                source_key = self._normalize_required(
                    source["source_key"],
                    "Source key",
                )
                applicability = self._normalize_required(
                    source["applicability"],
                    "Source applicability",
                )
            except KeyError as exc:
                raise InvalidContext(
                    "Source kind, key, and applicability are required"
                ) from exc
            confidentiality = self._enum(
                ContextConfidentiality,
                source.get(
                    "confidentiality",
                    ContextConfidentiality.PROJECT.value,
                ),
                "Source confidentiality",
            )
            source_owner_id = source.get("source_owner_id")
            if source_owner_id is not None:
                source_owner_id = self._require_active_user(
                    source_owner_id
                ).id
            if confidentiality == ContextConfidentiality.RESTRICTED:
                if source_owner_id != current_user.id:
                    raise ContextForbidden()
            revision = self._normalize_optional(
                source.get("revision")
            ) or "unrevisioned"
            identity = (kind.value, source_key, revision)
            if identity in identities:
                raise InvalidContext(
                    "Duplicate Context source reference"
                )
            identities.add(identity)
            normalized.append(
                {
                    "source_kind": kind.value,
                    "source_key": source_key,
                    "source_owner_id": source_owner_id,
                    "revision": revision,
                    "effective_at": source.get("effective_at"),
                    "observation_at": source.get("observation_at"),
                    "source_maturity": self._normalize_optional(
                        source.get("source_maturity")
                    ),
                    "confidentiality": confidentiality.value,
                    "applicability": applicability,
                    "limitations": self._normalize_optional(
                        source.get("limitations")
                    ),
                }
            )
        return normalized

    def _require_contribution_access(
        self,
        *,
        project: Project,
        workspace: EngineeringWorkspace | None,
        current_user: User,
    ) -> None:
        if not self._is_active_actor(current_user):
            raise ContextForbidden()
        if current_user.role == "admin":
            return
        if current_user.id in {
            project.owner_id,
            project.primary_assignee_id,
        }:
            return
        if workspace is not None and self._workspace_participant(
            workspace,
            current_user.id,
        ):
            return
        raise ContextForbidden()

    @staticmethod
    def _workspace_participant(
        workspace: EngineeringWorkspace,
        user_id: int,
    ) -> bool:
        return (
            user_id
            in {
                workspace.owner_id,
                workspace.primary_assignee_id,
            }
            or any(
                membership.user_id == user_id
                for membership in workspace.memberships
            )
        )

    def _require_edit_access(
        self,
        context: EngineeringContext,
        current_user: User,
    ) -> None:
        if not self._is_active_actor(current_user):
            raise ContextForbidden()
        if current_user.id in {context.owner_id, context.steward_id}:
            return
        project = context.project
        workspace = context.workspace
        if current_user.id in {
            project.owner_id,
            project.primary_assignee_id,
        }:
            return
        if workspace is not None and self._workspace_participant(
            workspace,
            current_user.id,
        ):
            return
        raise ContextForbidden()

    def _require_governance_access(
        self,
        context: EngineeringContext,
        current_user: User,
    ) -> None:
        if not self._is_active_actor(current_user):
            raise ContextForbidden()
        if current_user.role == "admin":
            return
        if current_user.id == context.project.owner_id:
            return
        if (
            context.workspace is not None
            and current_user.id == context.workspace.owner_id
        ):
            return
        if current_user.id in {context.owner_id, context.steward_id}:
            return
        raise ContextForbidden()

    @staticmethod
    def _require_current(context: EngineeringContext) -> None:
        if context.lifecycle != ContextLifecycle.CURRENT.value:
            raise ContextLifecycleConflict(
                context.lifecycle,
                ContextLifecycle.CURRENT.value,
            )
        if (
            context.workspace is not None
            and context.workspace.status == WorkspaceStatus.ARCHIVED.value
        ):
            raise InvalidContext(
                "Archived Workspace Context is not operational"
            )

    def _audit_and_commit(
        self,
        *,
        current_user: User,
        action: str,
        context_id: int,
        details: dict,
    ) -> None:
        try:
            create_audit_log(
                db=self.db,
                user_id=current_user.id,
                action=action,
                entity="ENGINEERING_CONTEXT",
                entity_id=context_id,
                details=self._serialized(details),
            )
        except Exception:
            self.db.rollback()
            raise
        self.db.expire_all()

    @classmethod
    def _snapshot(cls, context: EngineeringContext) -> dict:
        return {
            "context_key": context.context_key,
            "kind": context.kind,
            "scope": context.scope,
            "project_id": context.project_id,
            "workspace_id": context.workspace_id,
            "owner_id": context.owner_id,
            "steward_id": context.steward_id,
            "authority": context.authority,
            "lifecycle": context.lifecycle,
            "purpose": context.purpose,
            "version": context.version,
            "payload": cls._payload_response(context),
        }

    @classmethod
    def _response(cls, context: EngineeringContext) -> dict:
        return {
            "id": context.id,
            **cls._snapshot(context),
            "withdrawal_reason": context.withdrawal_reason,
            "withdrawn_at": context.withdrawn_at,
            "subjects": [
                {
                    "id": subject.id,
                    "subject_kind": subject.subject_kind,
                    "project_id": subject.subject_project_id,
                    "workspace_id": subject.subject_workspace_id,
                    "discipline": subject.discipline,
                }
                for subject in context.subject_references
            ],
            "sources": [
                cls._source_response(source)
                for source in context.source_references
            ],
            "created_by_id": context.created_by_id,
            "created_at": context.created_at,
            "updated_at": context.updated_at,
        }

    @staticmethod
    def _payload_response(context: EngineeringContext) -> dict | None:
        if context.facts is not None:
            return {
                "statement": context.facts.statement,
                "uncertainty": context.facts.uncertainty,
            }
        if context.engineering_value is not None:
            value = context.engineering_value
            return {
                "numeric_value": value.numeric_value,
                "unit": value.unit,
                "quantity_type": value.quantity_type,
                "tolerance_min": value.tolerance_min,
                "tolerance_max": value.tolerance_max,
                "range_min": value.range_min,
                "range_max": value.range_max,
                "basis": value.basis,
                "condition_type": value.condition_type,
                "condition": value.condition,
                "uncertainty": value.uncertainty,
            }
        if context.assumption is not None:
            return {
                "statement": context.assumption.statement,
                "reason": context.assumption.reason,
                "consequence": context.assumption.consequence,
                "confirmation_condition": (
                    context.assumption.confirmation_condition
                ),
            }
        return None

    @classmethod
    def _source_response(
        cls,
        source: EngineeringContextSourceReference,
    ) -> dict:
        return {
            "id": source.id,
            "source_kind": source.source_kind,
            "source_key": source.source_key,
            "source_owner_id": source.source_owner_id,
            "revision": source.revision,
            "effective_at": source.effective_at,
            "observation_at": source.observation_at,
            "source_maturity": source.source_maturity,
            "confidentiality": source.confidentiality,
            "applicability": source.applicability,
            "limitations": source.limitations,
        }

    @staticmethod
    def _safe_source(values: dict) -> dict:
        return {
            "source_kind": values["source_kind"],
            "source_key": values["source_key"],
            "source_owner_id": values["source_owner_id"],
            "revision": values["revision"],
            "confidentiality": values["confidentiality"],
            "applicability": values["applicability"],
            "limitations": values["limitations"],
        }

    @classmethod
    def _serialized(cls, value):
        if isinstance(value, dict):
            return {
                key: cls._serialized(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [cls._serialized(item) for item in value]
        if isinstance(value, (datetime, Decimal)):
            return str(value)
        return value

    @staticmethod
    def _enum(enum_type, value, label):
        try:
            return value if isinstance(value, enum_type) else enum_type(value)
        except (TypeError, ValueError) as exc:
            raise InvalidContext(f"Unsupported {label}") from exc

    @staticmethod
    def _normalize_required(value, label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise InvalidContext(f"{label} is required")
        return value.strip()

    @staticmethod
    def _normalize_optional(value) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise InvalidContext("Context text must be a string")
        value = value.strip()
        return value or None

    @staticmethod
    def _is_active_actor(user: User) -> bool:
        return (
            user.is_active
            and user.role in {"admin", "engineer"}
        )

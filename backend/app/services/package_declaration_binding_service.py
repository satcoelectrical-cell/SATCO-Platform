"""Governed Context/Evidence bindings and deterministic package readiness."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from uuid import UUID, uuid4

from sqlalchemy import and_, exists, func, select

from app.discipline_packages.descriptors.eic_v1 import DESCRIPTORS_V1
from app.models.audit_log import AuditLog
from app.models.engineering_context import (
    EngineeringContext,
    EngineeringContextFact,
    EngineeringContextSourceReference,
    EngineeringContextSubjectReference,
    EngineeringContextValue,
)
from app.models.engineering_deliverable import (
    EngineeringDeliverable,
    EngineeringDeliverableHistory,
    EngineeringDeliverableIdempotency,
    EngineeringDeliverableOutbox,
    EngineeringDeliverableRevision,
)
from app.models.engineering_object import EngineeringObject
from app.models.evidence import Evidence
from app.models.evidence_command import EvidenceOutbox
from app.models.package_input_binding import (
    EngineeringContextPackageInputBinding,
    EvidencePackageInputBinding,
)
from app.repositories.patch_052_operation_unit_of_work import Patch052OperationUnitOfWork
from app.schemas.discipline_package_operations import (
    PackageContextBindingResponse,
    PackageContextEvaluationResponse,
    PackageContextResult,
    PackageEvidenceBindingResponse,
    PackageEvidenceResult,
    PackageReadinessResponse,
)
from app.services.electrical_package_service import (
    PackageConflict,
    PackageDeclarationMismatch,
    PackageProtectedNotFound,
    PackageUnavailable,
    _retry_package_races,
)
from app.services.patch_052_mutation_guard import (
    Patch052MutationProtected,
    Patch052MutationUnavailable,
    lock_owner_mutation_scope,
    lock_package_context,
)


_VALUE_CONTEXTS = {
    "electrical.system_voltage_basis", "electrical.load_duty_basis",
    "instrumentation.operating_range", "instrumentation.design_conditions",
}


def _digest(value) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


class PackageDeclarationBindingService:
    """Shared owner-side binding service; package facts remain descriptor-owned."""

    def __init__(self, session_factory, *, package_key: str):
        if package_key not in {"electrical", "instrumentation", "control_automation"}:
            raise ValueError("unsupported operational package")
        self._session_factory = session_factory
        self.package_key = package_key
        self.descriptor = next(d for d in DESCRIPTORS_V1 if d.package_key == package_key)

    def _locked_context(self, uow, **scope):
        try:
            return lock_package_context(uow, package_key=self.package_key, **scope)
        except Patch052MutationProtected as exc:
            raise PackageProtectedNotFound() from exc
        except Patch052MutationUnavailable as exc:
            raise PackageUnavailable() from exc

    def _preauthorize(self, *, actor_id, organization_id, auth_version, project_id,
                      workspace_id, context_subject=None, evidence_ids=(), object_ids=(),
                      deliverable_revision=None):
        """Owner-only precheck before any package/declaration resolution."""
        with Patch052OperationUnitOfWork(self._session_factory) as uow:
            try:
                lock_owner_mutation_scope(
                    uow.session, actor_id=actor_id, organization_id=organization_id,
                    auth_version=auth_version, project_id=project_id,
                    workspace_id=workspace_id,
                )
            except Patch052MutationProtected as exc:
                raise PackageProtectedNotFound() from exc
            if context_subject is not None:
                context_id, subject_id = context_subject
                row = uow.session.execute(select(
                    EngineeringContextSubjectReference, EngineeringContext,
                ).join(
                    EngineeringContext,
                    EngineeringContext.id == EngineeringContextSubjectReference.context_id,
                ).where(
                    EngineeringContextSubjectReference.id == subject_id,
                    EngineeringContext.id == context_id,
                    EngineeringContext.project_id == project_id,
                    EngineeringContext.workspace_id == workspace_id,
                    ~EngineeringContext.source_references.any(and_(
                        EngineeringContextSourceReference.confidentiality == "restricted",
                        EngineeringContextSourceReference.source_owner_id != actor_id,
                    )),
                )).first()
                if row is None: raise PackageProtectedNotFound()
            if object_ids:
                rows = list(uow.session.scalars(select(EngineeringObject.id).where(
                    EngineeringObject.id.in_(object_ids),
                    EngineeringObject.organization_id == organization_id,
                    EngineeringObject.project_id == project_id,
                    EngineeringObject.workspace_id == workspace_id,
                )))
                if len(rows) != len(object_ids): raise PackageProtectedNotFound()
            if evidence_ids:
                rows = list(uow.session.scalars(select(Evidence.id).where(
                    Evidence.id.in_(evidence_ids), Evidence.organization_id == organization_id,
                    Evidence.project_id == project_id,
                    (Evidence.workspace_id.is_(None)) | (Evidence.workspace_id == workspace_id),
                )))
                if len(rows) != len(evidence_ids): raise PackageProtectedNotFound()
            if deliverable_revision is not None:
                deliverable_id, revision_id = deliverable_revision
                row = uow.session.execute(select(EngineeringDeliverable, EngineeringDeliverableRevision).join(
                    EngineeringDeliverableRevision,
                    EngineeringDeliverableRevision.deliverable_id == EngineeringDeliverable.id,
                ).where(
                    EngineeringDeliverable.id == deliverable_id,
                    EngineeringDeliverableRevision.id == revision_id,
                    EngineeringDeliverable.organization_id == organization_id,
                    EngineeringDeliverable.project_id == project_id,
                    EngineeringDeliverable.workspace_id == workspace_id,
                )).first()
                if row is None: raise PackageProtectedNotFound()

    def _input(self, input_id: str, source_kind: str):
        row = next((i for i in self.descriptor.contributions.engineering_inputs
                    if i.id == input_id and i.source_kind == source_kind), None)
        if row is None: raise PackageDeclarationMismatch()
        return row

    def _context_declaration(self, input_row):
        rows = [d for d in self.descriptor.contributions.context_contributions
                if d.context_kind_id == input_row.input_type_id]
        if len(rows) != 1: raise PackageDeclarationMismatch()
        return rows[0]

    def _evidence_requirement(self, input_row):
        rows = [d for d in self.descriptor.contributions.evidence_requirements
                if d.id == input_row.input_type_id]
        if len(rows) != 1: raise PackageDeclarationMismatch()
        return rows[0]

    def _audit(self, session, *, actor_id, action, entity_id=None, entity_uuid=None,
               correlation_id, locked, declaration_id, source_version):
        session.add(AuditLog(
            user_id=actor_id, action=action, entity="PACKAGE_INPUT_BINDING",
            entity_id=entity_id, entity_uuid=entity_uuid,
            details={
                "package_key": self.package_key,
                "package_version": locked.selection.package_version,
                "descriptor_digest": locked.selection.descriptor_digest,
                "registry_digest": locked.registry.registry_digest,
                "project_configuration_revision": locked.selection.configuration_revision,
                "declaration_id": declaration_id,
                "source_version": source_version,
                "correlation_id": str(correlation_id), "outcome": "success",
            },
        ))

    def _request_fingerprint(self, operation, *, organization_id, project_id,
                             workspace_id, data, **identifiers):
        return _digest({
            "operation": operation,
            "organization_id": organization_id,
            "project_id": project_id,
            "workspace_id": workspace_id,
            "package_key": self.package_key,
            "identifiers": identifiers,
            "data": data.model_dump(mode="json"),
        })

    @staticmethod
    def _prior_idempotency(uow, *, organization_id, actor_id, operation,
                           idempotency_key, fingerprint):
        prior = uow.deliverables.get_idempotency(
            organization_id=organization_id, actor_id=actor_id,
            operation=operation, idempotency_key=idempotency_key,
        )
        if prior is not None and prior.fingerprint != fingerprint:
            raise PackageConflict()
        return prior

    @staticmethod
    def _stage_idempotency(uow, *, organization_id, actor_id, operation,
                           idempotency_key, fingerprint, replay_json, now):
        uow.deliverables.add(EngineeringDeliverableIdempotency(
            id=uuid4(), organization_id=organization_id, actor_id=actor_id,
            operation=operation, idempotency_key=idempotency_key,
            fingerprint=fingerprint, replay_json=replay_json, created_at=now,
        ))

    @_retry_package_races
    def bind_context(self, *, actor_id, organization_id, auth_version=1, project_id,
                     workspace_id, data, correlation_id, idempotency_key):
        self._preauthorize(
            actor_id=actor_id, organization_id=organization_id, auth_version=auth_version,
            project_id=project_id, workspace_id=workspace_id,
            context_subject=(data.context_id, data.context_subject_reference_id),
        )
        with Patch052OperationUnitOfWork(self._session_factory) as uow:
            locked = self._locked_context(
                uow, actor_id=actor_id, organization_id=organization_id,
                auth_version=auth_version, project_id=project_id, workspace_id=workspace_id,
            )
            if data.expected_configuration_revision != locked.selection.configuration_revision:
                raise PackageConflict()
            operation = f"{self.package_key}_ctx_binding"
            fingerprint = self._request_fingerprint(
                operation, organization_id=organization_id,
                project_id=project_id, workspace_id=workspace_id, data=data,
            )
            prior = self._prior_idempotency(
                uow, organization_id=organization_id, actor_id=actor_id,
                operation=operation, idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if prior is not None:
                return PackageContextBindingResponse(**prior.replay_json["result"])
            source = uow.session.execute(select(
                EngineeringContextSubjectReference, EngineeringContext,
            ).join(
                EngineeringContext,
                EngineeringContext.id == EngineeringContextSubjectReference.context_id,
            ).where(
                EngineeringContextSubjectReference.id == data.context_subject_reference_id,
                EngineeringContext.id == data.context_id,
                EngineeringContext.project_id == project_id,
                EngineeringContext.workspace_id == workspace_id,
                ~EngineeringContext.source_references.any(and_(
                    EngineeringContextSourceReference.confidentiality == "restricted",
                    EngineeringContextSourceReference.source_owner_id != actor_id,
                )),
            ).with_for_update()).first()
            if source is None: raise PackageProtectedNotFound()
            subject, context = source
            if context.lifecycle != "current" or context.version != data.expected_context_version:
                raise PackageConflict()
            input_row = self._input(data.input_declaration_id, "context")
            declaration = self._context_declaration(input_row)
            if subject.subject_kind not in declaration.allowed_subject_kind_ids:
                raise PackageDeclarationMismatch()
            if subject.subject_kind == "workspace":
                if subject.subject_workspace_id != workspace_id: raise PackageDeclarationMismatch()
            elif subject.subject_kind == "engineering_object":
                obj = uow.session.scalar(select(EngineeringObject).where(
                    EngineeringObject.id == subject.subject_engineering_object_id,
                    EngineeringObject.organization_id == organization_id,
                    EngineeringObject.project_id == project_id,
                    EngineeringObject.workspace_id == workspace_id,
                ).with_for_update())
                if obj is None: raise PackageProtectedNotFound()
            else:
                raise PackageDeclarationMismatch()
            expected_kind = "qualified_engineering_value" if input_row.input_type_id in _VALUE_CONTEXTS else "qualified_fact"
            if context.kind != expected_kind: raise PackageDeclarationMismatch()
            payload_model = EngineeringContextValue if expected_kind == "qualified_engineering_value" else EngineeringContextFact
            if uow.session.get(payload_model, context.id) is None:
                raise PackageDeclarationMismatch()
            identity = (
                subject.id, context.version, project_id,
                locked.selection.configuration_revision, self.package_key, input_row.id,
            )
            row = uow.bindings.context_exact(identity)
            if row is None:
                current_count = uow.session.scalar(select(func.count()).select_from(
                    EngineeringContextPackageInputBinding,
                ).join(
                    EngineeringContextSubjectReference,
                    EngineeringContextSubjectReference.id
                    == EngineeringContextPackageInputBinding.context_subject_reference_id,
                ).join(
                    EngineeringContext,
                    EngineeringContext.id
                    == EngineeringContextSubjectReference.context_id,
                ).where(
                    EngineeringContextPackageInputBinding.project_id == project_id,
                    EngineeringContextPackageInputBinding.project_configuration_revision
                    == locked.selection.configuration_revision,
                    EngineeringContextPackageInputBinding.package_key == self.package_key,
                    EngineeringContextPackageInputBinding.input_declaration_id == input_row.id,
                    EngineeringContext.version
                    == EngineeringContextPackageInputBinding.context_version,
                    EngineeringContext.lifecycle == "current",
                ))
                if current_count >= input_row.max_occurrences:
                    raise PackageDeclarationMismatch()
                row = EngineeringContextPackageInputBinding(
                    context_subject_reference_id=subject.id, context_version=context.version,
                    project_id=project_id,
                    project_configuration_revision=locked.selection.configuration_revision,
                    package_key=self.package_key, input_declaration_id=input_row.id,
                    bound_by_id=actor_id, bound_at=datetime.now(timezone.utc),
                )
                uow.bindings.add_context(row)
                self._audit(
                    uow.session, actor_id=actor_id, action="PackageContextInputBound",
                    entity_id=context.id, correlation_id=correlation_id, locked=locked,
                    declaration_id=input_row.id, source_version=context.version,
                )
            result = PackageContextBindingResponse(
                context_id=context.id, context_version=context.version,
                context_subject_reference_id=subject.id, project_id=project_id,
                workspace_id=context.workspace_id, package_key=self.package_key,
                package_version=locked.selection.package_version,
                descriptor_digest=locked.selection.descriptor_digest,
                project_configuration_revision=locked.selection.configuration_revision,
                input_declaration_id=input_row.id,
                context_declaration_id=declaration.id, bound_at=row.bound_at,
            )
            self._stage_idempotency(
                uow, organization_id=organization_id, actor_id=actor_id,
                operation=operation, idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                replay_json={"schema": "package-context-binding.v1",
                             "result": result.model_dump(mode="json")},
                now=datetime.now(timezone.utc),
            )
            uow.commit()
            return result

    @_retry_package_races
    def bind_evidence(self, *, actor_id, organization_id, auth_version=1, project_id,
                      workspace_id, data, correlation_id, idempotency_key):
        self._preauthorize(
            actor_id=actor_id, organization_id=organization_id, auth_version=auth_version,
            project_id=project_id, workspace_id=workspace_id,
            evidence_ids=(data.evidence_id,),
        )
        with Patch052OperationUnitOfWork(self._session_factory) as uow:
            locked = self._locked_context(
                uow, actor_id=actor_id, organization_id=organization_id,
                auth_version=auth_version, project_id=project_id, workspace_id=workspace_id,
            )
            if data.expected_configuration_revision != locked.selection.configuration_revision:
                raise PackageConflict()
            operation = f"{self.package_key}_ev_binding"
            fingerprint = self._request_fingerprint(
                operation, organization_id=organization_id,
                project_id=project_id, workspace_id=workspace_id, data=data,
            )
            prior = self._prior_idempotency(
                uow, organization_id=organization_id, actor_id=actor_id,
                operation=operation, idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if prior is not None:
                return PackageEvidenceBindingResponse(**prior.replay_json["result"])
            evidence = uow.session.scalar(select(Evidence).where(
                Evidence.id == data.evidence_id, Evidence.organization_id == organization_id,
                Evidence.project_id == project_id,
                (Evidence.workspace_id.is_(None)) | (Evidence.workspace_id == workspace_id),
            ).with_for_update())
            if evidence is None: raise PackageProtectedNotFound()
            if (evidence.version != data.expected_evidence_version
                    or evidence.lifecycle != "current" or evidence.source_standing != "current"):
                raise PackageConflict()
            input_row = self._input(data.input_declaration_id, "evidence")
            requirement = self._evidence_requirement(input_row)
            if evidence.source_kind != requirement.evidence_kind_id:
                raise PackageDeclarationMismatch()
            verified = uow.session.scalar(select(exists().where(
                EvidenceOutbox.aggregate_id == evidence.id,
                EvidenceOutbox.aggregate_version == evidence.version,
                EvidenceOutbox.event_type == "EvidenceLifecycleTransitioned",
            )))
            if requirement.human_verification_required and not verified:
                raise PackageDeclarationMismatch()
            identity = (
                evidence.id, evidence.version, project_id,
                locked.selection.configuration_revision, self.package_key, input_row.id,
            )
            row = uow.bindings.evidence_exact(identity)
            if row is None:
                current_count = uow.session.scalar(select(func.count()).select_from(
                    EvidencePackageInputBinding,
                ).join(
                    Evidence,
                    Evidence.id == EvidencePackageInputBinding.evidence_id,
                ).where(
                    EvidencePackageInputBinding.project_id == project_id,
                    EvidencePackageInputBinding.project_configuration_revision
                    == locked.selection.configuration_revision,
                    EvidencePackageInputBinding.package_key == self.package_key,
                    EvidencePackageInputBinding.input_declaration_id == input_row.id,
                    Evidence.version == EvidencePackageInputBinding.evidence_version,
                    Evidence.lifecycle == "current",
                    Evidence.source_standing == "current",
                ))
                if current_count >= input_row.max_occurrences:
                    raise PackageDeclarationMismatch()
                row = EvidencePackageInputBinding(
                    evidence_id=evidence.id, evidence_version=evidence.version,
                    project_id=project_id,
                    project_configuration_revision=locked.selection.configuration_revision,
                    package_key=self.package_key, input_declaration_id=input_row.id,
                    bound_by_id=actor_id, bound_at=datetime.now(timezone.utc),
                )
                uow.bindings.add_evidence(row)
                self._audit(
                    uow.session, actor_id=actor_id, action="PackageEvidenceInputBound",
                    entity_uuid=evidence.id, correlation_id=correlation_id, locked=locked,
                    declaration_id=input_row.id, source_version=evidence.version,
                )
            result = PackageEvidenceBindingResponse(
                evidence_id=evidence.id, evidence_version=evidence.version,
                project_id=project_id, workspace_id=evidence.workspace_id,
                package_key=self.package_key,
                package_version=locked.selection.package_version,
                descriptor_digest=locked.selection.descriptor_digest,
                project_configuration_revision=locked.selection.configuration_revision,
                input_declaration_id=input_row.id,
                evidence_requirement_id=requirement.id, bound_at=row.bound_at,
            )
            self._stage_idempotency(
                uow, organization_id=organization_id, actor_id=actor_id,
                operation=operation, idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                replay_json={"schema": "package-evidence-binding.v1",
                             "result": result.model_dump(mode="json")},
                now=datetime.now(timezone.utc),
            )
            uow.commit()
            return result

    def _context_results(self, session, *, actor_id, organization_id, project_id,
                         workspace_id, revision, objects, required_input_ids=None):
        required_filter = None if required_input_ids is None else set(required_input_ids)
        object_declarations = {(d.family_id, d.id.rsplit(".", 1)[-1]): d
                               for d in self.descriptor.contributions.object_types}
        needed = []
        for obj in objects:
            declaration = object_declarations.get((obj.family, obj.object_type))
            if declaration is None: continue
            for kind_id in declaration.required_context_kind_ids:
                input_row = next(i for i in self.descriptor.contributions.engineering_inputs
                                 if i.source_kind == "context" and i.input_type_id == kind_id)
                context_declaration = self._context_declaration(input_row)
                if (context_declaration.allowed_subject_kind_ids == ("engineering_object",)
                        and (required_filter is None or input_row.id in required_filter)):
                    needed.append((input_row, "engineering_object", str(obj.id)))
        for input_row in self.descriptor.contributions.engineering_inputs:
            if input_row.source_kind != "context" or (required_filter is not None and input_row.id not in required_filter):
                continue
            declaration = self._context_declaration(input_row)
            if declaration.allowed_subject_kind_ids == ("workspace",):
                needed.append((input_row, "workspace", str(workspace_id)))
        input_ids = tuple(row.id for row in sorted(
            {item[0].id: item[0] for item in needed}.values(),
            key=lambda row: (row.ordinal, row.id),
        ))
        rows = [] if not input_ids else list(session.execute(select(
            EngineeringContextPackageInputBinding,
            EngineeringContextSubjectReference,
            EngineeringContext,
        ).join(
            EngineeringContextSubjectReference,
            EngineeringContextSubjectReference.id == EngineeringContextPackageInputBinding.context_subject_reference_id,
        ).join(
            EngineeringContext, EngineeringContext.id == EngineeringContextSubjectReference.context_id,
        ).where(
            EngineeringContextPackageInputBinding.project_id == project_id,
            EngineeringContextPackageInputBinding.project_configuration_revision == revision,
            EngineeringContextPackageInputBinding.package_key == self.package_key,
            EngineeringContextPackageInputBinding.input_declaration_id.in_(input_ids),
        )))
        by_target = {}
        hidden_targets = set()
        for binding, subject, context in rows:
            target = str(subject.subject_engineering_object_id if subject.subject_kind == "engineering_object" else subject.subject_workspace_id)
            key = (binding.input_declaration_id, subject.subject_kind, target)
            hidden = session.scalar(select(exists().where(
                EngineeringContextSourceReference.context_id == context.id,
                EngineeringContextSourceReference.confidentiality == "restricted",
                EngineeringContextSourceReference.source_owner_id != actor_id,
            )))
            if hidden:
                hidden_targets.add(key); continue
            by_target.setdefault(key, []).append((binding, context))
        if hidden_targets:
            raise PackageProtectedNotFound()
        results = []
        for input_row, subject_kind, subject_id in sorted(
            needed, key=lambda item: (item[0].ordinal, item[1], item[2]),
        ):
            declaration = self._context_declaration(input_row)
            key = (input_row.id, subject_kind, subject_id)
            candidates = by_target.get(key, [])
            current = [(b, c) for b, c in candidates if c.lifecycle == "current" and c.version == b.context_version]
            if current:
                for binding, context in sorted(current, key=lambda item: (item[1].id, item[1].version)):
                    results.append(PackageContextResult(
                        input_declaration_id=input_row.id, context_declaration_id=declaration.id,
                        context_kind_id=declaration.context_kind_id, subject_kind=subject_kind,
                        subject_id=subject_id, required=True, context_id=context.id,
                        context_version=context.version, status="SATISFIED", reason_code=None,
                    ))
            else:
                status = "INDETERMINATE" if key in hidden_targets else ("STALE" if candidates else "MISSING")
                reason = "protected_source_unavailable" if key in hidden_targets else ("binding_source_version_stale" if candidates else "required_binding_missing")
                results.append(PackageContextResult(
                    input_declaration_id=input_row.id, context_declaration_id=declaration.id,
                    context_kind_id=declaration.context_kind_id, subject_kind=subject_kind,
                    subject_id=subject_id, required=True, context_id=None,
                    context_version=None, status=status, reason_code=reason,
                ))
        return tuple(results), tuple(input_ids)

    def _status(self, context_results, evidence_results=()):
        statuses = [r.status for r in (*context_results, *evidence_results)]
        if "INDETERMINATE" in statuses: return "INDETERMINATE"
        if any(s != "SATISFIED" for s in statuses): return "FINDINGS"
        return "PASS"

    def evaluate_context(self, *, actor_id, organization_id, auth_version=1,
                         project_id, workspace_id, expected_configuration_revision,
                         object_ids, correlation_id):
        object_ids = tuple(sorted(set(object_ids), key=str))
        if len(object_ids) > 64: raise PackageDeclarationMismatch()
        self._preauthorize(
            actor_id=actor_id, organization_id=organization_id, auth_version=auth_version,
            project_id=project_id, workspace_id=workspace_id, object_ids=object_ids,
        )
        with Patch052OperationUnitOfWork(self._session_factory) as uow:
            started = datetime.now(timezone.utc)
            locked = self._locked_context(
                uow, actor_id=actor_id, organization_id=organization_id,
                auth_version=auth_version, project_id=project_id, workspace_id=workspace_id,
            )
            if expected_configuration_revision != locked.selection.configuration_revision:
                raise PackageConflict()
            objects = list(uow.session.scalars(select(EngineeringObject).where(
                EngineeringObject.id.in_(object_ids),
                EngineeringObject.organization_id == organization_id,
                EngineeringObject.project_id == project_id,
                EngineeringObject.workspace_id == workspace_id,
            ).order_by(EngineeringObject.id).with_for_update(read=True)))
            if len(objects) != len(object_ids): raise PackageProtectedNotFound()
            results, input_ids = self._context_results(
                uow.session, actor_id=actor_id, organization_id=organization_id,
                project_id=project_id, workspace_id=workspace_id,
                revision=locked.selection.configuration_revision, objects=objects,
            )
            completed = datetime.now(timezone.utc)
            status = self._status(results)
            return PackageContextEvaluationResponse(
                project_id=project_id, workspace_id=workspace_id,
                package_key=self.package_key, package_version=locked.selection.package_version,
                descriptor_digest=locked.selection.descriptor_digest,
                project_configuration_revision=locked.selection.configuration_revision,
                status=status, object_ids=object_ids, required_input_ids=input_ids,
                context_results=results,
                findings=tuple(sorted({r.reason_code for r in results if r.reason_code})),
                limitations=("protected_source_unavailable",) if status == "INDETERMINATE" else (),
                observation_started_at=started, observation_completed_at=completed,
                source_version_digest=_digest([(r.context_id, r.context_version, r.status) for r in results]),
            )

    def _readiness_locked(self, session, *, locked, actor_id, organization_id,
                          project_id, workspace_id, deliverable_id, revision_id,
                          object_ids, evidence_ids, target_standing):
        started = datetime.now(timezone.utc)
        pair = session.execute(select(EngineeringDeliverable, EngineeringDeliverableRevision).join(
            EngineeringDeliverableRevision,
            EngineeringDeliverableRevision.deliverable_id == EngineeringDeliverable.id,
        ).where(
            EngineeringDeliverable.id == deliverable_id,
            EngineeringDeliverableRevision.id == revision_id,
            EngineeringDeliverable.organization_id == organization_id,
            EngineeringDeliverable.project_id == project_id,
            EngineeringDeliverable.workspace_id == workspace_id,
        ).with_for_update()).first()
        if pair is None: raise PackageProtectedNotFound()
        deliverable, revision = pair
        declaration = next((d for d in self.descriptor.contributions.deliverables
                            if d.id == deliverable.origin_declaration_id
                            and d.deliverable_type_id == deliverable.deliverable_type), None)
        if (declaration is None or deliverable.origin_package_key != self.package_key
                or deliverable.origin_project_configuration_revision != locked.selection.configuration_revision):
            raise PackageDeclarationMismatch()
        issue = target_standing == "issued"
        if issue:
            fourth = next(d for d in self.descriptor.contributions.evidence_requirements
                          if d.applicable_operation_id == f"{self.package_key}.deliverable_issue")
            required_inputs = (next(i.id for i in self.descriptor.contributions.engineering_inputs
                                    if i.source_kind == "evidence" and i.input_type_id == fourth.id),)
            context_results = ()
        else:
            required_inputs = declaration.required_input_ids
            context_input_ids = tuple(i for i in required_inputs if any(
                d.id == i and d.source_kind == "context"
                for d in self.descriptor.contributions.engineering_inputs
            ))
            objects = list(session.scalars(select(EngineeringObject).where(
                EngineeringObject.id.in_(object_ids),
                EngineeringObject.organization_id == organization_id,
                EngineeringObject.project_id == project_id,
                EngineeringObject.workspace_id == workspace_id,
            ).order_by(EngineeringObject.id).with_for_update(read=True)))
            if len(objects) != len(object_ids): raise PackageProtectedNotFound()
            context_results, _ = self._context_results(
                session, actor_id=actor_id, organization_id=organization_id,
                project_id=project_id, workspace_id=workspace_id,
                revision=locked.selection.configuration_revision, objects=objects,
                required_input_ids=context_input_ids,
            )
        evidence_inputs = tuple(i for i in required_inputs if any(
            d.id == i and d.source_kind == "evidence"
            for d in self.descriptor.contributions.engineering_inputs
        ))
        bindings = session.execute(select(EvidencePackageInputBinding, Evidence).join(
            Evidence, Evidence.id == EvidencePackageInputBinding.evidence_id,
        ).where(
            EvidencePackageInputBinding.project_id == project_id,
            EvidencePackageInputBinding.project_configuration_revision == locked.selection.configuration_revision,
            EvidencePackageInputBinding.package_key == self.package_key,
            EvidencePackageInputBinding.input_declaration_id.in_(evidence_inputs),
            EvidencePackageInputBinding.evidence_id.in_(evidence_ids) if evidence_ids else False,
            Evidence.organization_id == organization_id,
        )).all() if evidence_inputs else []
        by_input = {}
        for binding, evidence in bindings:
            by_input.setdefault(binding.input_declaration_id, []).append((binding, evidence))
        evidence_results = []
        for input_id in evidence_inputs:
            input_row = self._input(input_id, "evidence")
            requirement = self._evidence_requirement(input_row)
            candidates = by_input.get(input_id, [])
            valid = []
            stale = False
            for binding, evidence in candidates:
                if (evidence.version != binding.evidence_version or evidence.lifecycle != "current"
                        or evidence.source_standing != "current"):
                    stale = True; continue
                verified = session.scalar(select(exists().where(
                    EvidenceOutbox.aggregate_id == evidence.id,
                    EvidenceOutbox.aggregate_version == evidence.version,
                    EvidenceOutbox.event_type == "EvidenceLifecycleTransitioned",
                )))
                if not verified: stale = True; continue
                if issue and (evidence.source_kind != "human_review"
                              or evidence.source_reference.lower() != str(deliverable.id)
                              or evidence.source_revision.lower() != str(revision.id)):
                    stale = True; continue
                valid.append((binding, evidence))
            if len(valid) >= requirement.minimum_count:
                for binding, evidence in sorted(valid, key=lambda item: str(item[1].id)):
                    evidence_results.append(PackageEvidenceResult(
                        input_declaration_id=input_id, evidence_requirement_id=requirement.id,
                        evidence_kind_id=requirement.evidence_kind_id,
                        minimum_count=requirement.minimum_count, evidence_id=evidence.id,
                        evidence_version=evidence.version, status="SATISFIED", reason_code=None,
                    ))
            else:
                evidence_results.append(PackageEvidenceResult(
                    input_declaration_id=input_id, evidence_requirement_id=requirement.id,
                    evidence_kind_id=requirement.evidence_kind_id,
                    minimum_count=requirement.minimum_count, evidence_id=None,
                    evidence_version=None, status="STALE" if stale else "MISSING",
                    reason_code=("human_review_revision_mismatch" if issue and stale
                                 else "binding_source_version_stale" if stale
                                 else "required_binding_missing"),
                ))
        evidence_results = tuple(evidence_results)
        missing_object_selection = bool(context_input_ids) and not object_ids if not issue else False
        status = self._status(context_results, evidence_results)
        if missing_object_selection:
            status = "FINDINGS"
        state_valid = revision.sequence == deliverable.current_revision_sequence and (
            (target_standing == "ready_for_review" and revision.standing == "draft")
            or (target_standing == "issued" and revision.standing == "reviewed")
        )
        if not state_valid: status = "FINDINGS"
        completed = datetime.now(timezone.utc)
        source_digest = _digest({
            "deliverable": [str(deliverable.id), deliverable.version],
            "revision": [str(revision.id), revision.version],
            "contexts": [(r.context_id, r.context_version, r.status) for r in context_results],
            "evidence": [(r.evidence_id, r.evidence_version, r.status) for r in evidence_results],
        })
        return PackageReadinessResponse(
            project_id=project_id, workspace_id=workspace_id,
            deliverable_id=deliverable.id, revision_id=revision.id,
            deliverable_version=deliverable.version, revision_version=revision.version,
            package_key=self.package_key, package_version=locked.selection.package_version,
            descriptor_digest=locked.selection.descriptor_digest,
            project_configuration_revision=locked.selection.configuration_revision,
            status=status, required_input_ids=required_inputs,
            context_results=context_results, evidence_results=evidence_results,
            transition_allowed=status == "PASS" and state_valid,
            findings=tuple(sorted(
                {r.reason_code for r in (*context_results, *evidence_results) if r.reason_code}
                | ({"required_binding_missing"} if missing_object_selection else set())
            )),
            limitations=(), observation_started_at=started,
            observation_completed_at=completed,
            rule_hook_id=f"{self.package_key}.deliverable_readiness",
            source_version_digest=source_digest,
        ), deliverable, revision

    def readiness(self, *, actor_id, organization_id, auth_version=1, project_id,
                  workspace_id, deliverable_id, revision_id,
                  expected_configuration_revision, object_ids, evidence_ids,
                  correlation_id):
        object_ids = tuple(sorted(set(object_ids), key=str))
        evidence_ids = tuple(sorted(set(evidence_ids), key=str))
        if len(object_ids) > 64 or len(evidence_ids) > 24: raise PackageDeclarationMismatch()
        self._preauthorize(
            actor_id=actor_id, organization_id=organization_id, auth_version=auth_version,
            project_id=project_id, workspace_id=workspace_id, object_ids=object_ids,
            evidence_ids=evidence_ids,
            deliverable_revision=(deliverable_id, revision_id),
        )
        with Patch052OperationUnitOfWork(self._session_factory) as uow:
            locked = self._locked_context(
                uow, actor_id=actor_id, organization_id=organization_id,
                auth_version=auth_version, project_id=project_id, workspace_id=workspace_id,
            )
            if expected_configuration_revision != locked.selection.configuration_revision:
                raise PackageConflict()
            pair = uow.session.get(EngineeringDeliverableRevision, revision_id)
            target = "issued" if pair is not None and pair.standing == "reviewed" else "ready_for_review"
            if target == "issued" and len(evidence_ids) > 8:
                raise PackageDeclarationMismatch()
            return self._readiness_locked(
                uow.session, locked=locked, actor_id=actor_id,
                organization_id=organization_id, project_id=project_id,
                workspace_id=workspace_id, deliverable_id=deliverable_id,
                revision_id=revision_id, object_ids=object_ids,
                evidence_ids=evidence_ids, target_standing=target,
            )[0]

    @_retry_package_races
    def transition(self, *, actor_id, organization_id, auth_version=1, project_id,
                   workspace_id, deliverable_id, revision_id, data,
                   correlation_id, idempotency_key):
        self._preauthorize(
            actor_id=actor_id, organization_id=organization_id, auth_version=auth_version,
            project_id=project_id, workspace_id=workspace_id, object_ids=data.object_ids,
            evidence_ids=data.evidence_ids,
            deliverable_revision=(deliverable_id, revision_id),
        )
        with Patch052OperationUnitOfWork(self._session_factory) as uow:
            locked = self._locked_context(
                uow, actor_id=actor_id, organization_id=organization_id,
                auth_version=auth_version, project_id=project_id, workspace_id=workspace_id,
            )
            if data.expected_configuration_revision != locked.selection.configuration_revision:
                raise PackageConflict()
            operation = (
                "pkg_control_auto_transition"
                if self.package_key == "control_automation"
                else f"{self.package_key}_pkg_transition"
            )
            fingerprint = self._request_fingerprint(
                operation, organization_id=organization_id,
                project_id=project_id, workspace_id=workspace_id, data=data,
                deliverable_id=deliverable_id, revision_id=revision_id,
            )
            prior = self._prior_idempotency(
                uow, organization_id=organization_id, actor_id=actor_id,
                operation=operation, idempotency_key=idempotency_key,
                fingerprint=fingerprint,
            )
            if prior is not None:
                outbox_id = prior.replay_json.get("outbox_id")
                outbox = None if outbox_id is None else uow.session.get(
                    EngineeringDeliverableOutbox, UUID(outbox_id),
                )
                if (outbox is None or outbox.deliverable_id != deliverable_id
                        or outbox.event_type != "PackageDeliverableRevisionTransitioned"
                        or "replay" not in outbox.payload):
                    raise PackageConflict()
                return PackageReadinessResponse(**outbox.payload["replay"])
            readiness, deliverable, revision = self._readiness_locked(
                uow.session, locked=locked, actor_id=actor_id,
                organization_id=organization_id, project_id=project_id,
                workspace_id=workspace_id, deliverable_id=deliverable_id,
                revision_id=revision_id, object_ids=data.object_ids,
                evidence_ids=data.evidence_ids, target_standing=data.target_standing,
            )
            if (not readiness.transition_allowed
                    or deliverable.version != data.expected_deliverable_version
                    or revision.version != data.expected_revision_version):
                raise PackageConflict()
            now = datetime.now(timezone.utc)
            revision.standing = data.target_standing
            revision.version += 1
            revision.transitioned_by_id = actor_id
            revision.transitioned_at = now
            deliverable.version += 1
            deliverable.standing = data.target_standing
            deliverable.updated_by_id = actor_id
            deliverable.updated_at = now
            result = readiness.model_copy(update={
                "deliverable_version": deliverable.version,
                "revision_version": revision.version,
                "transition_allowed": False,
            })
            uow.session.add(EngineeringDeliverableHistory(
                id=uuid4(), deliverable_id=deliverable.id,
                organization_id=organization_id, aggregate_version=deliverable.version,
                event_type="package_revision_transitioned", revision_id=revision.id,
                revision_target_standing=data.target_standing,
                workspace_id_at_event=deliverable.workspace_id,
                workspace_scope_recorded=True,
                actor_id=actor_id, occurred_at=now,
            ))
            outbox = EngineeringDeliverableOutbox(
                id=uuid4(), event_id=uuid4(), deliverable_id=deliverable.id,
                aggregate_version=deliverable.version,
                event_type="PackageDeliverableRevisionTransitioned",
                payload={
                    "package_key": self.package_key,
                    "project_configuration_revision": locked.selection.configuration_revision,
                    "target_standing": data.target_standing,
                    "source_version_digest": readiness.source_version_digest,
                    "correlation_id": str(correlation_id),
                    "replay": result.model_dump(mode="json"),
                }, occurred_at=now,
            )
            uow.session.add(outbox)
            self._stage_idempotency(
                uow, organization_id=organization_id, actor_id=actor_id,
                operation=operation, idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                replay_json={"schema": "package-transition.v1",
                             "outbox_id": str(outbox.id)}, now=now,
            )
            self._audit(
                uow.session, actor_id=actor_id, action="PackageDeliverableTransition",
                entity_uuid=deliverable.id, correlation_id=correlation_id, locked=locked,
                declaration_id=deliverable.origin_declaration_id,
                source_version=deliverable.version,
            )
            uow.commit()
            return result

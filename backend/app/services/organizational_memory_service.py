"""PATCH-034 Organizational Memory application orchestration."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from datetime import timedelta
from uuid import UUID, uuid4

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from sqlalchemy.exc import IntegrityError

from app.core.config import settings

from app.enums.organizational_memory import MemoryEventType, MemoryOperation, MemoryProvenanceOperation, MemoryRejectionReason, MemoryStanding
from app.exceptions.organizational_memory import (
    OrganizationalMemoryIntegrityError, OrganizationalMemoryInvalidLineage,
    OrganizationalMemoryInvalidStanding, OrganizationalMemoryValidationError,
    OrganizationalMemoryVersionConflict,
)
from app.models.organizational_memory import OrganizationalMemory
from app.models.organizational_memory_command import (
    AcceptedReportProjection, AcceptedReportProtectedNotFound, AcceptedReportUnavailable,
    ActiveMemoryCriteria, ActiveMemoryDetail, ActiveMemoryHistory,
    ActiveMemoryPage, ActiveMemorySummary, AuthorizedMemoryLink,
    AdmissionSuccess, AdmitAcceptedReport, CaptureProvenanceAuthorization,
    CreateMemorySuccessor, CreateSuccessorSuccess,
    EngineeringObjectProvenanceAuthorization,
    EngineeringRelationshipProvenanceAuthorization,
    EvidenceProvenanceAuthorization, MemoryAuditRecord,
    MemoryAuthorizationRequest, MemoryDuplicateSource, MemoryFinalRecheckRequest,
    MemoryIdempotencyCompleted, MemoryIdempotencyConflict, MemoryIdempotencyKey,
    MemoryIdempotencyMiss, MemoryInvalidRequest, MemoryInvalidStanding,
    MemoryOutboxRecord, MemoryProtectedNotFound, MemoryRejectionAuditRecord,
    MemoryProvenanceAuthorizationRequest, MemoryUnavailable,
    GetActiveMemory, GetActiveSuccess, InspectHistorySuccess,
    InspectMemoryHistory, ListActiveMemory, ListActiveSuccess, MemoryOrderingAnchor,
    MemoryVersionConflict, ProvenanceAuthorized, ProvenanceProtectedNotFound,
    ProvenanceUnavailable, StoredAdmissionResultV1, StoredSuccessorResultV1,
    StoredSupersessionResultV1, StoredWithdrawalResultV1, SupersedeMemory,
    SupersededMemoryHistory, SupersessionSuccess, WithdrawMemory,
    WithdrawalSuccess, WithdrawnMemoryHistory,
    admission_material_from_snapshot, canonical_digest,
)
from app.models.technical_report_command import (
    CaptureHistoricalBasisV1, EvidenceHistoricalBasisV1,
    EngineeringObjectHistoricalBasisV1,
    EngineeringRelationshipHistoricalBasisV1,
)
from app.repositories.organizational_memory_unit_of_work import MemoryAuthorizationDenied


class MemoryDependencyUnavailable(Exception):
    """Internal dependency failure translated to the closed unavailable result."""


class OrganizationalMemoryService:
    def __init__(self, uow_factory, accepted_reports, provenance, clock):
        self.uow_factory = uow_factory; self.accepted_reports = accepted_reports
        self.provenance = provenance; self.clock = clock

    def get_active(self, actor, request: GetActiveMemory):
        try:
            with self.uow_factory() as uow:
                memory = uow.memories.get_scoped(request.memory_id, actor.organization_id)
                if memory is None or memory.standing is not MemoryStanding.ACTIVE:
                    raise MemoryAuthorizationDenied()
                authorization = self._read_authorization(
                    actor, MemoryOperation.GET_ACTIVE, memory,
                )
                uow.authorization.require(authorization)
                source = self._source(actor, memory.source, self._scope(memory))
                if isinstance(source, MemoryUnavailable): return source
                if not isinstance(source, AcceptedReportProjection):
                    raise MemoryAuthorizationDenied()
                safe_provenance = self._read_provenance(
                    actor, memory, source, request.include_provenance,
                    MemoryProvenanceOperation.REUSE
                    if request.reuse_intent else MemoryProvenanceOperation.GET_ACTIVE,
                )
                if not isinstance(safe_provenance, tuple): return safe_provenance
                return GetActiveSuccess(
                    "success", ActiveMemoryDetail(
                        self._summary(memory), memory.projection,
                        memory.admission_rationale, memory.reuse_restrictions,
                        safe_provenance,
                    ),
                )
        except MemoryAuthorizationDenied: return MemoryProtectedNotFound()
        except OrganizationalMemoryValidationError: return MemoryInvalidRequest()
        except Exception: return MemoryUnavailable()

    def inspect_history(self, actor, request: InspectMemoryHistory):
        try:
            with self.uow_factory() as uow:
                memory = uow.memories.get_scoped(request.memory_id, actor.organization_id)
                if memory is None: raise MemoryAuthorizationDenied()
                uow.authorization.require(self._read_authorization(
                    actor, MemoryOperation.INSPECT_HISTORY, memory,
                ))
                source = self._source(actor, memory.source, self._scope(memory))
                if isinstance(source, MemoryUnavailable): return source
                if not isinstance(source, AcceptedReportProjection):
                    raise MemoryAuthorizationDenied()
                safe_provenance = self._read_provenance(
                    actor, memory, source, request.include_provenance,
                    MemoryProvenanceOperation.INSPECT_HISTORY,
                )
                if not isinstance(safe_provenance, tuple): return safe_provenance
                predecessor = self._protected_link(
                    uow, actor, memory.predecessor_memory_id,
                    request.include_predecessor,
                )
                replacement = self._protected_link(
                    uow, actor, memory.replacement_memory_id,
                    request.include_replacement,
                )
                common = (
                    memory.id, memory.version, memory.standing, memory.source,
                    memory.projection, memory.admitted_by_id, memory.admitted_at,
                    predecessor, safe_provenance,
                )
                if memory.standing is MemoryStanding.ACTIVE:
                    detail = ActiveMemoryHistory(*common)
                elif memory.standing is MemoryStanding.WITHDRAWN:
                    detail = WithdrawnMemoryHistory(
                        memory.id, memory.version, memory.standing,
                        memory.source, memory.projection,
                        memory.admitted_by_id, memory.admitted_at,
                        memory.withdrawn_by_id, memory.withdrawn_at,
                        memory.withdrawal_reason, predecessor, safe_provenance,
                    )
                else:
                    detail = SupersededMemoryHistory(
                        memory.id, memory.version, memory.standing,
                        memory.source, memory.projection,
                        memory.admitted_by_id, memory.admitted_at,
                        memory.superseded_by_id, memory.superseded_at,
                        memory.supersession_reason, predecessor, replacement,
                        safe_provenance,
                    )
                return InspectHistorySuccess("success", detail)
        except MemoryAuthorizationDenied: return MemoryProtectedNotFound()
        except OrganizationalMemoryValidationError: return MemoryInvalidRequest()
        except Exception: return MemoryUnavailable()

    def list_active(self, actor, request: ListActiveMemory):
        try:
            anchor = self._decode_continuation(actor, request)
            with self.uow_factory() as uow:
                uow.authorization.require(MemoryAuthorizationRequest(
                    actor, MemoryOperation.LIST_ACTIVE, request.scope, None,
                    None, None, None, (),
                ))
                visible = []; evaluated = rounds = calls = 0
                may_continue = False
                while len(visible) < request.page_size and rounds < 10 and evaluated < 100:
                    limit = min(request.page_size, 100 - evaluated)
                    candidates = uow.memories.list_active(ActiveMemoryCriteria(
                        actor.organization_id, request.scope.workspace_id,
                        request.scope.project_id, None, anchor, limit,
                    ))
                    rounds += 1
                    if not candidates.items:
                        may_continue = False
                        break
                    for memory in candidates.items:
                        if evaluated >= 100 or len(visible) >= request.page_size:
                            may_continue = True
                            break
                        evaluated += 1
                        anchor = MemoryOrderingAnchor(memory.admitted_at, memory.id)
                        try:
                            uow.authorization.require(self._read_authorization(
                                actor, MemoryOperation.LIST_ACTIVE, memory,
                            ))
                            calls += 1
                            source = self._source(
                                actor, memory.source, self._scope(memory),
                            )
                            if isinstance(source, AcceptedReportProjection):
                                visible.append(self._summary(memory))
                        except MemoryAuthorizationDenied:
                            pass
                    else:
                        may_continue = candidates.has_more
                    if len(visible) >= request.page_size or evaluated >= 100:
                        may_continue = may_continue or candidates.has_more
                        break
                    if not candidates.has_more:
                        may_continue = False
                        break
                if rounds >= 10 and anchor is not None:
                    may_continue = True
                token = (
                    self._encode_continuation(actor, request, anchor)
                    if may_continue and anchor is not None else None
                )
                page = ActiveMemoryPage(tuple(visible), len(visible), token)
                return ListActiveSuccess("success", page)
        except MemoryAuthorizationDenied: return MemoryProtectedNotFound()
        except (
            OrganizationalMemoryValidationError, ValueError, KeyError,
            TypeError, InvalidTag,
        ):
            return MemoryInvalidRequest()
        except Exception: return MemoryUnavailable()

    def admit(self, command: AdmitAcceptedReport):
        return self._admit(command, None)

    def create_successor(self, command: CreateMemorySuccessor):
        return self._admit(command, command.predecessor_memory_id)

    def _admit(self, command, predecessor_id):
        operation = MemoryOperation.ADMIT if predecessor_id is None else MemoryOperation.CREATE_SUCCESSOR
        try:
            source = self._source(command.metadata.actor, command.source, command.scope)
            if not isinstance(source, AcceptedReportProjection): return source
            projection, manifest = admission_material_from_snapshot(source.snapshot)
            provenance_result = self._provenance(command.metadata.actor, command.source, command.scope, source.snapshot, operation)
            if not isinstance(provenance_result, ProvenanceAuthorized): return self._provenance_result(provenance_result)
        except (OrganizationalMemoryValidationError, OrganizationalMemoryIntegrityError):
            return MemoryInvalidRequest()
        except Exception:
            return MemoryUnavailable()
        fingerprint = canonical_digest(command); key = self._key(command, operation)
        now = self.clock.now()
        try:
            with self.uow_factory() as uow:
                authorization = MemoryAuthorizationRequest(
                    command.metadata.actor, operation, command.scope, None,
                    command.source, predecessor_id, None, command.audience_actor_ids,
                )
                uow.authorization.require(authorization, source.owner_id)
                replay = self._replay(uow, key, fingerprint, command, source.owner_id)
                if replay is not None: return replay
                reservation = self._reserve(uow, key, fingerprint, command, source.owner_id)
                if reservation is not None: return reservation
                existing = uow.memories.get_by_source(command.source, command.scope.organization_id)
                if existing is not None:
                    uow.authorization.require(MemoryAuthorizationRequest(
                        command.metadata.actor, operation, self._scope(existing),
                        existing.id, existing.source, predecessor_id, None,
                        existing.audience_actor_ids,
                    ), source.owner_id)
                    uow.rollback(); return MemoryDuplicateSource()
                predecessor = None
                if predecessor_id is not None:
                    predecessor = uow.memories.lock_scoped(predecessor_id, command.scope.organization_id)
                    if predecessor is None: raise MemoryAuthorizationDenied()
                repeated = self._source(command.metadata.actor, command.source, command.scope)
                if isinstance(repeated, MemoryUnavailable):
                    raise MemoryDependencyUnavailable()
                if not isinstance(repeated, AcceptedReportProjection): raise MemoryAuthorizationDenied()
                repeated_provenance = self._provenance(command.metadata.actor, command.source, command.scope, repeated.snapshot, operation)
                if isinstance(repeated_provenance, ProvenanceUnavailable):
                    raise MemoryDependencyUnavailable()
                if not isinstance(repeated_provenance, ProvenanceAuthorized): raise MemoryAuthorizationDenied()
                uow.final_recheck.require_current(MemoryFinalRecheckRequest(
                    authorization, None, None if predecessor is None else predecessor.version,
                    None, command.source.accepted_snapshot_digest,
                ), repeated.owner_id)
                memory_id = uuid4()
                if predecessor is None:
                    memory = OrganizationalMemory.admit(
                        memory_id=memory_id, projection=projection, manifest=manifest,
                        admitted_by_id=command.metadata.actor.actor_id, admitted_at=now,
                        admission_rationale=command.admission_rationale,
                        audience_actor_ids=command.audience_actor_ids,
                        reuse_restrictions=command.reuse_restrictions,
                    )
                else:
                    memory = OrganizationalMemory.create_successor(
                        predecessor=predecessor, memory_id=memory_id,
                        projection=projection, manifest=manifest,
                        admitted_by_id=command.metadata.actor.actor_id, admitted_at=now,
                        admission_rationale=command.admission_rationale,
                        audience_actor_ids=command.audience_actor_ids,
                        reuse_restrictions=command.reuse_restrictions,
                    )
                event_id = uuid4(); history = memory.initial_history(event_id=event_id)
                event = memory.event(
                    event_id=event_id, event_type=MemoryEventType.ADMITTED,
                    actor_id=command.metadata.actor.actor_id, occurred_at=now,
                    command_id=command.metadata.command_id,
                    correlation_id=command.metadata.correlation_id,
                    causation_id=command.metadata.command_id,
                )
                uow.memories.add(memory); uow.memories.append_history(history)
                self._stage(uow, command, operation, memory, None, event, now)
                stored = (
                    StoredAdmissionResultV1("admit.v1", memory.id, 1, "active", command.source.report_id, command.source.accepted_aggregate_version)
                    if predecessor is None else
                    StoredSuccessorResultV1("create_successor.v1", memory.id, 1, "active", command.source.report_id, command.source.accepted_aggregate_version, predecessor.id)
                )
                uow.idempotency.record_result(key, fingerprint, stored)
                uow.flush(); uow.commit()
                return self._outward(stored, command)
        except MemoryAuthorizationDenied:
            self._rejection(uow, command, operation, MemoryRejectionReason.OPERATION_DENIED, predecessor_id)
            return MemoryProtectedNotFound()
        except (OrganizationalMemoryValidationError, OrganizationalMemoryIntegrityError, OrganizationalMemoryInvalidLineage):
            return MemoryInvalidRequest()
        except OrganizationalMemoryVersionConflict:
            return MemoryVersionConflict()
        except IntegrityError:
            return self._duplicate_after_race(command, operation, predecessor_id, source.owner_id)
        except MemoryDependencyUnavailable:
            return MemoryUnavailable()
        except Exception:
            return MemoryUnavailable()

    def withdraw(self, command: WithdrawMemory):
        operation = MemoryOperation.WITHDRAW
        try:
            with self.uow_factory() as uow:
                memory = uow.memories.lock_scoped(command.memory_id, command.metadata.actor.organization_id)
                if memory is None: raise MemoryAuthorizationDenied()
                authorization = self._authorization(command, operation, memory)
                source = self._source(command.metadata.actor, memory.source, self._scope(memory))
                if isinstance(source, MemoryUnavailable):
                    raise MemoryDependencyUnavailable()
                if not isinstance(source, AcceptedReportProjection): raise MemoryAuthorizationDenied()
                uow.authorization.require(authorization, source.owner_id)
                key = self._key(command, operation); fingerprint = canonical_digest(command)
                replay = self._replay(uow, key, fingerprint, command, source.owner_id)
                if replay is not None: return replay
                reservation = self._reserve(uow, key, fingerprint, command, source.owner_id)
                if reservation is not None: return reservation
                repeated = self._source(command.metadata.actor, memory.source, self._scope(memory))
                if isinstance(repeated, MemoryUnavailable):
                    raise MemoryDependencyUnavailable()
                if not isinstance(repeated, AcceptedReportProjection):
                    raise MemoryAuthorizationDenied()
                repeated_provenance = self._provenance(
                    command.metadata.actor, memory.source, self._scope(memory),
                    repeated.snapshot, operation,
                )
                if isinstance(repeated_provenance, ProvenanceUnavailable):
                    raise MemoryDependencyUnavailable()
                if not isinstance(repeated_provenance, ProvenanceAuthorized):
                    raise MemoryAuthorizationDenied()
                uow.final_recheck.require_current(MemoryFinalRecheckRequest(
                    authorization, command.expected_version, None, None,
                    memory.source.accepted_snapshot_digest,
                ), repeated.owner_id)
                now = self.clock.now(); updated, history = memory.withdraw(
                    expected_version=command.expected_version,
                    actor_id=command.metadata.actor.actor_id,
                    occurred_at=now, reason=command.reason,
                )
                if not uow.memories.persist_standing_expected_version(updated, command.expected_version):
                    raise OrganizationalMemoryVersionConflict()
                event = updated.event(
                    event_id=history.event_id, event_type=MemoryEventType.WITHDRAWN,
                    actor_id=command.metadata.actor.actor_id, occurred_at=now,
                    command_id=command.metadata.command_id,
                    correlation_id=command.metadata.correlation_id,
                    causation_id=command.metadata.command_id,
                )
                uow.memories.append_history(history)
                self._stage(uow, command, operation, updated, memory.version, event, now)
                stored = StoredWithdrawalResultV1("withdraw.v1", updated.id, updated.version, "withdrawn", now)
                uow.idempotency.record_result(key, fingerprint, stored)
                uow.flush(); uow.commit(); return self._outward(stored, command)
        except OrganizationalMemoryVersionConflict: return MemoryVersionConflict()
        except OrganizationalMemoryInvalidStanding: return MemoryInvalidStanding()
        except MemoryAuthorizationDenied:
            self._rejection(uow, command, operation, MemoryRejectionReason.OPERATION_DENIED, command.memory_id)
            return MemoryProtectedNotFound()
        except MemoryDependencyUnavailable: return MemoryUnavailable()
        except Exception: return MemoryUnavailable()

    def supersede(self, command: SupersedeMemory):
        operation = MemoryOperation.SUPERSEDE
        try:
            with self.uow_factory() as uow:
                pair = uow.memories.lock_pair_scoped(
                    command.predecessor_memory_id, command.replacement_memory_id,
                    command.metadata.actor.organization_id,
                )
                if pair is None: raise MemoryAuthorizationDenied()
                predecessor, replacement = pair
                authorization = self._authorization(command, operation, predecessor, replacement)
                # Supersession combines withdraw authority for the predecessor
                # with admit authority for the replacement source.
                uow.authorization.require(authorization, None)
                source_views = []
                for item in (predecessor, replacement):
                    source = self._source(command.metadata.actor, item.source, self._scope(item))
                    if isinstance(source, MemoryUnavailable):
                        raise MemoryDependencyUnavailable()
                    if not isinstance(source, AcceptedReportProjection): raise MemoryAuthorizationDenied()
                    source_views.append(source)
                uow.authorization.require(authorization, source_views[1].owner_id)
                key = self._key(command, operation); fingerprint = canonical_digest(command)
                replay = self._replay(uow, key, fingerprint, command, source_views[1].owner_id)
                if replay is not None: return replay
                reservation = self._reserve(
                    uow, key, fingerprint, command, source_views[1].owner_id,
                )
                if reservation is not None: return reservation
                final_source_views = []
                for item in (predecessor, replacement):
                    source = self._source(command.metadata.actor, item.source, self._scope(item))
                    if isinstance(source, MemoryUnavailable):
                        raise MemoryDependencyUnavailable()
                    if not isinstance(source, AcceptedReportProjection):
                        raise MemoryAuthorizationDenied()
                    provenance = self._provenance(
                        command.metadata.actor, item.source, self._scope(item),
                        source.snapshot, operation,
                    )
                    if isinstance(provenance, ProvenanceUnavailable):
                        raise MemoryDependencyUnavailable()
                    if not isinstance(provenance, ProvenanceAuthorized):
                        raise MemoryAuthorizationDenied()
                    final_source_views.append(source)
                uow.final_recheck.require_current(MemoryFinalRecheckRequest(
                    authorization, None, command.expected_predecessor_version,
                    command.expected_replacement_version,
                    predecessor.source.accepted_snapshot_digest,
                ), final_source_views[1].owner_id)
                now = self.clock.now(); updated, history = predecessor.supersede_with(
                    replacement, expected_version=command.expected_predecessor_version,
                    expected_replacement_version=command.expected_replacement_version,
                    actor_id=command.metadata.actor.actor_id, occurred_at=now,
                    reason=command.reason,
                )
                if not uow.memories.persist_standing_expected_version(updated, command.expected_predecessor_version):
                    raise OrganizationalMemoryVersionConflict()
                event = updated.event(
                    event_id=history.event_id, event_type=MemoryEventType.SUPERSEDED,
                    actor_id=command.metadata.actor.actor_id, occurred_at=now,
                    command_id=command.metadata.command_id,
                    correlation_id=command.metadata.correlation_id,
                    causation_id=command.metadata.command_id,
                )
                uow.memories.append_history(history)
                self._stage(uow, command, operation, updated, predecessor.version, event, now)
                stored = StoredSupersessionResultV1(
                    "supersede.v1", predecessor.id, updated.version, "superseded",
                    replacement.id, replacement.version, "active", now,
                )
                uow.idempotency.record_result(key, fingerprint, stored)
                uow.flush(); uow.commit(); return self._outward(stored, command)
        except OrganizationalMemoryVersionConflict: return MemoryVersionConflict()
        except OrganizationalMemoryInvalidStanding: return MemoryInvalidStanding()
        except (MemoryAuthorizationDenied, OrganizationalMemoryInvalidLineage):
            self._rejection(uow, command, operation, MemoryRejectionReason.PROTECTED_LINEAGE_DENIED, command.predecessor_memory_id)
            return MemoryProtectedNotFound()
        except MemoryDependencyUnavailable: return MemoryUnavailable()
        except Exception: return MemoryUnavailable()

    def _source(self, actor, source, scope):
        result = self.accepted_reports.read_authorized_accepted(actor, source)
        if isinstance(result, AcceptedReportProtectedNotFound): return MemoryProtectedNotFound()
        if isinstance(result, AcceptedReportUnavailable): return MemoryUnavailable()
        if result.scope != scope: return MemoryProtectedNotFound()
        return result

    @staticmethod
    def _scope(memory):
        from app.models.organizational_memory_command import MemoryScope
        return MemoryScope(
            memory.organization_id, memory.workspace_id, memory.project_id,
        )

    @staticmethod
    def _summary(memory):
        return ActiveMemorySummary(
            memory.id, memory.version, MemoryStanding.ACTIVE,
            memory.source.report_id, memory.source.accepted_aggregate_version,
            memory.projection.purpose, memory.organization_id,
            memory.workspace_id, memory.project_id, memory.admitted_by_id,
            memory.admitted_at, memory.updated_at,
        )

    def _read_authorization(self, actor, operation, memory):
        return MemoryAuthorizationRequest(
            actor, operation, self._scope(memory), memory.id, memory.source,
            None, None, memory.audience_actor_ids,
        )

    def _read_provenance(self, actor, memory, source, requested, operation):
        if not requested:
            return ()
        result = self._provenance(
            actor, memory.source, self._scope(memory), source.snapshot,
            operation,
        )
        if isinstance(result, ProvenanceAuthorized):
            return result.items
        return self._provenance_result(result)

    def _protected_link(self, uow, actor, identity, requested):
        if not requested or identity is None:
            return None
        linked = uow.memories.get_scoped(identity, actor.organization_id)
        if linked is None:
            return None
        try:
            uow.authorization.require(self._read_authorization(
                actor, MemoryOperation.INSPECT_HISTORY, linked,
            ))
            source = self._source(actor, linked.source, self._scope(linked))
            if not isinstance(source, AcceptedReportProjection):
                return None
            return AuthorizedMemoryLink(linked.id)
        except Exception:
            return None

    @staticmethod
    def _token_key():
        return hashlib.sha256(
            (settings.SECRET_KEY + ":organizational-memory-continuation:v1").encode()
        ).digest()

    @staticmethod
    def _query_binding(actor, request):
        raw = json.dumps({
            "actor_id": actor.actor_id,
            "organization_id": str(actor.organization_id),
            "workspace_id": request.scope.workspace_id,
            "project_id": request.scope.project_id,
            "page_size": request.page_size,
        }, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    def _encode_continuation(self, actor, request, anchor):
        issued = self.clock.now()
        payload = json.dumps({
            "v": 1,
            "exp": int((issued + timedelta(minutes=15)).timestamp()),
            "actor_id": actor.actor_id,
            "organization_id": str(actor.organization_id),
            "workspace_id": request.scope.workspace_id,
            "project_id": request.scope.project_id,
            "page_size": request.page_size,
            "query_fingerprint": self._query_binding(actor, request),
            "anchor": {
                "admitted_at": anchor.admitted_at.isoformat(),
                "memory_id": str(anchor.memory_id),
            },
        }, sort_keys=True, separators=(",", ":")).encode()
        nonce = os.urandom(12)
        encrypted = AESGCM(self._token_key()).encrypt(
            nonce, payload, b"organizational-memory-continuation.v1",
        )
        return base64.urlsafe_b64encode(nonce + encrypted).decode().rstrip("=")

    def _decode_continuation(self, actor, request):
        if request.continuation is None:
            return None
        token = request.continuation
        padded = token + "=" * (-len(token) % 4)
        raw = base64.b64decode(padded, altchars=b"-_", validate=True)
        if base64.urlsafe_b64encode(raw).decode().rstrip("=") != token:
            raise ValueError("non-canonical continuation")
        if len(raw) < 29:
            raise ValueError("invalid continuation")
        payload = json.loads(AESGCM(self._token_key()).decrypt(
            raw[:12], raw[12:], b"organizational-memory-continuation.v1",
        ))
        expected = {
            "v": 1,
            "actor_id": actor.actor_id,
            "organization_id": str(actor.organization_id),
            "workspace_id": request.scope.workspace_id,
            "project_id": request.scope.project_id,
            "page_size": request.page_size,
            "query_fingerprint": self._query_binding(actor, request),
        }
        if any(payload.get(key) != value for key, value in expected.items()):
            raise ValueError("continuation binding mismatch")
        if set(payload) != set(expected) | {"exp", "anchor"}:
            raise ValueError("continuation shape mismatch")
        if type(payload["exp"]) is not int or self.clock.now().timestamp() >= payload["exp"]:
            raise ValueError("continuation expired")
        if set(payload["anchor"]) != {"admitted_at", "memory_id"}:
            raise ValueError("continuation anchor mismatch")
        from datetime import datetime
        return MemoryOrderingAnchor(
            datetime.fromisoformat(payload["anchor"]["admitted_at"]),
            UUID(payload["anchor"]["memory_id"]),
        )

    def _provenance(self, actor, source, scope, snapshot, operation):
        items = []
        for entry in snapshot.provenance:
            basis = entry.locator; common = (entry.entry_id, entry.ordinal)
            if isinstance(basis, CaptureHistoricalBasisV1): item = CaptureProvenanceAuthorization(*common, basis.capture_id, basis.source_version, basis.organization_id, basis.project_id, basis.workspace_id, basis.engineering_object_id)
            elif isinstance(basis, EvidenceHistoricalBasisV1): item = EvidenceProvenanceAuthorization(*common, basis.evidence_id, basis.source_version, basis.organization_id, basis.project_id, basis.workspace_id)
            elif isinstance(basis, EngineeringObjectHistoricalBasisV1): item = EngineeringObjectProvenanceAuthorization(*common, basis.engineering_object_id, basis.source_version, basis.organization_id, basis.project_id, basis.workspace_id)
            elif isinstance(basis, EngineeringRelationshipHistoricalBasisV1): item = EngineeringRelationshipProvenanceAuthorization(*common, basis.engineering_relationship_id, basis.source_version, basis.organization_id, basis.project_id, basis.workspace_id, basis.source_object_id, basis.target_object_id)
            else: raise OrganizationalMemoryValidationError("unsupported provenance")
            items.append(item)
        provenance_operation = (
            operation if isinstance(operation, MemoryProvenanceOperation) else
            MemoryProvenanceOperation.ADMIT
            if operation in (MemoryOperation.ADMIT, MemoryOperation.CREATE_SUCCESSOR)
            else MemoryProvenanceOperation.REUSE
        )
        requests = tuple(MemoryProvenanceAuthorizationRequest(
            actor, provenance_operation, scope, source,
            tuple(items[index:index + 100]),
        ) for index in range(0, len(items), 100))
        return self.provenance.authorize_logical_operation(requests)

    @staticmethod
    def _provenance_result(result):
        return MemoryUnavailable() if isinstance(result, ProvenanceUnavailable) else MemoryProtectedNotFound()

    @staticmethod
    def _key(command, operation):
        return MemoryIdempotencyKey(command.metadata.actor.organization_id, command.metadata.actor.actor_id, operation.value, command.metadata.idempotency_id)

    def _replay(self, uow, key, fingerprint, command, source_owner_id):
        found = uow.idempotency.find(key)
        if isinstance(found, MemoryIdempotencyMiss): return None
        if not isinstance(found, MemoryIdempotencyCompleted) or found.request_fingerprint != fingerprint:
            return MemoryIdempotencyConflict()
        result = found.result
        memory_id = (
            result.predecessor_memory_id
            if isinstance(result, StoredSupersessionResultV1)
            else result.memory_id
        )
        memory = uow.memories.lock_scoped(memory_id, command.metadata.actor.organization_id)
        if memory is None:
            raise MemoryAuthorizationDenied()
        replacement_id = (
            result.replacement_memory_id
            if isinstance(result, StoredSupersessionResultV1)
            else None
        )
        predecessor_id = (
            result.predecessor_memory_id
            if isinstance(result, StoredSuccessorResultV1)
            else (memory.id if replacement_id is not None else None)
        )
        uow.authorization.require(MemoryAuthorizationRequest(
            command.metadata.actor, MemoryOperation(key.operation), self._scope(memory),
            memory.id, memory.source, predecessor_id, replacement_id,
            memory.audience_actor_ids,
        ), source_owner_id)
        return self._outward(found.result, command)

    def _reserve(self, uow, key, fingerprint, command, source_owner_id):
        try:
            uow.idempotency.reserve(key, fingerprint)
            return None
        except IntegrityError:
            # The unique idempotency key is the concurrency arbiter.  Only
            # after rollback may the losing transaction inspect/replay the
            # winner's bounded result.
            uow.rollback()
            replay = self._replay(uow, key, fingerprint, command, source_owner_id)
            return replay if replay is not None else MemoryUnavailable()

    def _duplicate_after_race(self, command, operation, predecessor_id, source_owner_id):
        try:
            with self.uow_factory() as uow:
                existing = uow.memories.get_by_source(
                    command.source, command.scope.organization_id,
                )
                if existing is None:
                    return MemoryUnavailable()
                uow.authorization.require(MemoryAuthorizationRequest(
                    command.metadata.actor, operation, self._scope(existing),
                    existing.id, existing.source, predecessor_id, None,
                    existing.audience_actor_ids,
                ), source_owner_id)
                return MemoryDuplicateSource()
        except MemoryAuthorizationDenied:
            return MemoryProtectedNotFound()
        except Exception:
            return MemoryUnavailable()

    @staticmethod
    def _outward(result, command):
        if isinstance(result, StoredAdmissionResultV1): return AdmissionSuccess("success", result.memory_id, 1, MemoryStanding.ACTIVE, command.source)
        if isinstance(result, StoredSuccessorResultV1): return CreateSuccessorSuccess("success", result.memory_id, 1, MemoryStanding.ACTIVE, command.source, result.predecessor_memory_id)
        if isinstance(result, StoredWithdrawalResultV1): return WithdrawalSuccess("success", result.memory_id, result.result_version, MemoryStanding.WITHDRAWN, result.withdrawn_at)
        return SupersessionSuccess("success", result.predecessor_memory_id, result.predecessor_result_version, MemoryStanding.SUPERSEDED, result.replacement_memory_id, result.replacement_version_at_command, MemoryStanding.ACTIVE, result.superseded_at)

    @staticmethod
    def _scope(memory):
        from app.models.organizational_memory_command import MemoryScope
        return MemoryScope(memory.organization_id, memory.workspace_id, memory.project_id)

    def _authorization(self, command, operation, memory, replacement=None):
        return MemoryAuthorizationRequest(
            command.metadata.actor, operation, self._scope(memory), memory.id,
            replacement.source if replacement is not None else memory.source,
            memory.id if replacement else None,
            None if replacement is None else replacement.id,
            memory.audience_actor_ids,
        )

    @staticmethod
    def _stage(uow, command, operation, memory, previous_version, event, now):
        audit = MemoryAuditRecord(
            operation, command.metadata.actor.actor_id, memory.organization_id,
            memory.id, previous_version, memory.version, memory.standing,
            memory.source.report_id, memory.source.accepted_aggregate_version,
            command.metadata.correlation_id, command.metadata.command_id,
            command.metadata.idempotency_id, now, memory.predecessor_memory_id,
            memory.replacement_memory_id, len(memory.manifest.provenance_entries),
        )
        uow.audit.record(audit)
        uow.domain_events.record((MemoryOutboxRecord(
            event.event_id, memory.id, memory.version, event.event_type, 1,
            event.payload, now, now,
        ),))

    def _rejection(self, uow, command, operation, reason, memory_id):
        try:
            uow.rejection_audit.record_rejection(MemoryRejectionAuditRecord(
                operation, reason, command.metadata.actor.actor_id,
                command.metadata.actor.organization_id,
                command.metadata.correlation_id, command.metadata.command_id,
                self.clock.now(), memory_id,
            ))
        except Exception:
            pass

    # Batch 5 operations intentionally absent.

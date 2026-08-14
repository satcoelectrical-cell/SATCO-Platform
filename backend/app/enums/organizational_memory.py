"""Closed PATCH-034 Organizational Memory vocabularies."""

from enum import StrEnum


class MemoryStanding(StrEnum):
    ACTIVE = "active"
    WITHDRAWN = "withdrawn"
    SUPERSEDED = "superseded"


class MemoryOperation(StrEnum):
    ADMIT = "admit"
    GET_ACTIVE = "get_active"
    LIST_ACTIVE = "list_active"
    INSPECT_HISTORY = "inspect_history"
    CREATE_SUCCESSOR = "create_successor"
    WITHDRAW = "withdraw"
    SUPERSEDE = "supersede"
    GOVERNANCE_AUDIT = "governance_audit"


class MemoryOutcomeCode(StrEnum):
    SUCCESS = "success"
    PROTECTED_NOT_FOUND = "protected_not_found"
    INVALID_REQUEST = "invalid_request"
    VERSION_CONFLICT = "version_conflict"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    INVALID_STANDING = "invalid_standing"
    DUPLICATE_SOURCE = "duplicate_source"
    UNAVAILABLE = "unavailable"


class MemoryProvenanceOperation(StrEnum):
    ADMIT = "admit"
    GET_ACTIVE = "get_active"
    INSPECT_HISTORY = "inspect_history"
    REUSE = "reuse"


class MemoryEventType(StrEnum):
    ADMITTED = "ORGANIZATIONAL_MEMORY_ADMITTED"
    WITHDRAWN = "ORGANIZATIONAL_MEMORY_WITHDRAWN"
    SUPERSEDED = "ORGANIZATIONAL_MEMORY_SUPERSEDED"


class MemoryRejectionReason(StrEnum):
    INACTIVE_ACTOR = "inactive_actor"
    INACTIVE_ORGANIZATION = "inactive_organization"
    MEMBERSHIP_DENIED = "membership_denied"
    CROSS_ORGANIZATION = "cross_organization"
    SCOPE_DENIED = "scope_denied"
    SOURCE_DENIED = "source_denied"
    PROVENANCE_DENIED = "provenance_denied"
    OPERATION_DENIED = "operation_denied"
    AUDIENCE_DENIED = "audience_denied"
    REVOKED_AUTHORITY = "revoked_authority"
    PROTECTED_LINEAGE_DENIED = "protected_lineage_denied"
    ACCEPTED_STATE_INTEGRITY_FAILURE = "accepted_state_integrity_failure"


IDEMPOTENCY_RESULT_TYPES: dict[str, str] = {
    MemoryOperation.ADMIT.value: "admit.v1",
    MemoryOperation.WITHDRAW.value: "withdraw.v1",
    MemoryOperation.CREATE_SUCCESSOR.value: "create_successor.v1",
    MemoryOperation.SUPERSEDE.value: "supersede.v1",
}

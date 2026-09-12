"""Closed PATCH-054 standards vocabularies."""

from enum import Enum


class _StandardsEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class CatalogScope(_StandardsEnum):
    GLOBAL_TRUSTED = "global_trusted"
    ORGANIZATION_PRIVATE = "organization_private"


class StandardStanding(_StandardsEnum):
    CURRENT = "current"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"
    UNKNOWN = "unknown"


class RightsBasis(_StandardsEnum):
    METADATA_ONLY = "metadata_only"
    CUSTOMER_SUPPLIED_DECLARED = "customer_supplied_declared"
    ORGANIZATION_LICENSE = "organization_license"
    OPEN_DISTRIBUTION = "open_distribution"
    INTERNALLY_AUTHORED = "internally_authored"
    UNKNOWN = "unknown"


class RightsStatus(_StandardsEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    UNKNOWN = "unknown"


class AIProcessingPermission(_StandardsEnum):
    PROHIBITED = "prohibited"
    LOCAL_ONLY = "local_only"
    APPROVED_PROCESSOR = "approved_processor"


class StandardsFailureCode(_StandardsEnum):
    NOT_FOUND = "NOT_FOUND"
    PROTECTED_NOT_FOUND = "PROTECTED_NOT_FOUND"
    INVALID_REQUEST = "INVALID_REQUEST"
    RIGHTS_UNKNOWN = "RIGHTS_UNKNOWN"
    RIGHTS_EXPIRED = "RIGHTS_EXPIRED"
    RIGHTS_REVOKED = "RIGHTS_REVOKED"
    CONTENT_UNAVAILABLE = "CONTENT_UNAVAILABLE"
    EDITION_UNRESOLVED = "EDITION_UNRESOLVED"
    SUPERSEDED = "SUPERSEDED"
    WITHDRAWN = "WITHDRAWN"
    AI_USE_NOT_PERMITTED = "AI_USE_NOT_PERMITTED"
    DISPLAY_NOT_PERMITTED = "DISPLAY_NOT_PERMITTED"
    INDEXING_NOT_PERMITTED = "INDEXING_NOT_PERMITTED"
    SOURCE_INCOMPLETE = "SOURCE_INCOMPLETE"
    INDETERMINATE = "INDETERMINATE"
    STALE_ASSERTION = "STALE_ASSERTION"
    CONFLICT = "CONFLICT"
    VERSION_CONFLICT = "VERSION_CONFLICT"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"
    AI_UNAVAILABLE = "AI_UNAVAILABLE"
    INVALID_AI_OUTPUT = "INVALID_AI_OUTPUT"
    LEGACY_STANDARD_LOCATOR_PROHIBITED = "LEGACY_STANDARD_LOCATOR_PROHIBITED"

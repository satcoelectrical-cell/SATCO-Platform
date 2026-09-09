"""Closed ADR-025 Engineering Identifier vocabulary."""

from enum import StrEnum


class EngineeringIdentifierLifecycle(StrEnum):
    CURRENT = "current"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


class EngineeringIdentifierPrimaryRole(StrEnum):
    PRIMARY = "primary"
    ALTERNATE = "alternate"


class EngineeringIdentifierIssuingScope(StrEnum):
    PROJECT = "project"
    WORKSPACE = "workspace"
    EXTERNAL_AUTHORITY = "external_authority"


NORMALIZATION_ALGORITHM_VERSION = "satco_identifier_nfkc_casefold_v1"

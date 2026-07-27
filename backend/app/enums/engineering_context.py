from __future__ import annotations

from enum import Enum


class ContextKind(str, Enum):
    SUBJECT_REFERENCE = "subject_reference"
    QUALIFIED_FACT = "qualified_fact"
    QUALIFIED_ENGINEERING_VALUE = "qualified_engineering_value"
    ASSUMPTION = "assumption"
    SOURCE_EVIDENCE_REFERENCE = "source_evidence_reference"


class ContextScope(str, Enum):
    PROJECT = "project"
    WORKSPACE = "workspace"


class ContextAuthority(str, Enum):
    AUTHORITATIVE_FACT = "authoritative_fact"
    ENGINEER_VERIFIED_FACT = "engineer_verified_fact"
    ASSUMPTION = "assumption"


class ContextLifecycle(str, Enum):
    CURRENT = "current"
    WITHDRAWN = "withdrawn"


class ContextSubjectKind(str, Enum):
    PROJECT = "project"
    WORKSPACE = "workspace"
    DISCIPLINE = "discipline"


class ContextSourceKind(str, Enum):
    CUSTOMER_DOCUMENT = "customer_document"
    CONTRACT = "contract"
    APPROVED_PROJECT_DOCUMENT = "approved_project_document"
    VENDOR_DOCUMENT = "vendor_document"
    SITE_SURVEY = "site_survey"
    STANDARD = "standard"
    CALCULATION = "calculation"
    ENGINEER_INPUT = "engineer_input"
    EXTERNAL_REFERENCE = "external_reference"
    HISTORICAL_PROJECT_EVIDENCE = "historical_project_evidence"


class ContextConfidentiality(str, Enum):
    PROJECT = "project"
    WORKSPACE = "workspace"
    RESTRICTED = "restricted"

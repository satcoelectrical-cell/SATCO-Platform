"""Closed PATCH-032 Technical Report vocabularies."""

from enum import StrEnum


class TechnicalReportLifecycle(StrEnum):
    DRAFT = "draft"
    ACCEPTED = "accepted"


class TechnicalReportPurpose(StrEnum):
    FIELD_EXPERIENCE = "field_experience"
    TROUBLESHOOTING = "troubleshooting"
    ENGINEERING_ANALYSIS = "engineering_analysis"
    TECHNICAL_RECOMMENDATION = "technical_recommendation"


class TechnicalReportSourceClass(StrEnum):
    CANONICAL_MATERIAL = "canonical_material"
    EXTERNAL_OR_HUMAN_MATERIAL = "external_or_human_material"
    STANDARDS_MATERIAL = "standards_material"
    CONTEXTUAL_NON_MATERIAL = "contextual_non_material"


class TechnicalReportSourceType(StrEnum):
    UNIVERSAL_CAPTURE = "universal_capture"
    EVIDENCE = "evidence"
    ENGINEERING_OBJECT = "engineering_object"
    ENGINEERING_RELATIONSHIP = "engineering_relationship"
    EXTERNAL_OR_HUMAN = "external_or_human"
    STANDARD = "standard"
    CONTEXTUAL = "contextual"


class TechnicalReportOwningCapability(StrEnum):
    """Canonical capability owners named by the IDS-032 source matrix."""

    UNIVERSAL_CAPTURE = "universal_capture"
    EVIDENCE = "evidence"
    ENGINEERING_OBJECT = "engineering_object"
    ENGINEERING_RELATIONSHIP = "engineering_relationship"


class TechnicalReportVerificationStatus(StrEnum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"


class TechnicalReportAvailabilityStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class TechnicalReportIntegrityAlgorithm(StrEnum):
    SHA256 = "sha256"

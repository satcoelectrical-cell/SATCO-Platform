"""Controlled Evidence Foundation vocabularies."""
from enum import StrEnum

class EvidenceLifecycle(StrEnum):
    PROPOSED="proposed"; CURRENT="current"; WITHDRAWN="withdrawn"; SUPERSEDED="superseded"; REJECTED="rejected"
class EvidenceSourceKind(StrEnum):
    ENGINEERING_RECORD="engineering_record"; EXTERNAL_REFERENCE="external_reference"; HUMAN_REVIEW="human_review"; TECHNICAL_DECISION="technical_decision"; STANDARD_REFERENCE="standard_reference"; INSPECTION_RECORD="inspection_record"; COMMISSIONING_RECORD="commissioning_record"
class EvidenceSourceStanding(StrEnum):
    DRAFT="draft"; CURRENT="current"; WITHDRAWN="withdrawn"; SUPERSEDED="superseded"

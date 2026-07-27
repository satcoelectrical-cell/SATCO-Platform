from enum import Enum


class ContextRelationshipMeaning(str, Enum):
    REQUIRES = "requires"
    PROVIDED_BY = "provided_by"
    CONSUMED_BY = "consumed_by"
    POTENTIALLY_AFFECTS = "potentially_affects"


class RelationshipLifecycle(str, Enum):
    CURRENT = "current"
    WITHDRAWN = "withdrawn"


class RelationshipEndpointKind(str, Enum):
    CONTEXT = "context"
    PROJECT = "project"
    WORKSPACE = "workspace"
    DISCIPLINE = "discipline"
    EXTERNAL_SOURCE = "external_source"


class CommitmentProviderKind(str, Enum):
    USER = "user"
    WORKSPACE = "workspace"
    EXTERNAL_SOURCE = "external_source"


class InterfaceCommitmentState(str, Enum):
    IDENTIFIED = "identified"
    ACKNOWLEDGED_BY_PROVIDER = "acknowledged_by_provider"
    INFORMATION_PROVIDED = "information_provided"
    CONSUMER_REVIEW_REQUIRED = "consumer_review_required"
    FULFILLED_FOR_STATED_USE = "fulfilled_for_stated_use"
    REJECTED = "rejected"
    DISPUTED = "disputed"
    SUPERSEDED = "superseded"


class CommitmentCriticality(str, Enum):
    ROUTINE = "routine"
    IMPORTANT = "important"
    CRITICAL = "critical"

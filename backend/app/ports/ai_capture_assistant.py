"""Application-owned contracts for PATCH-035."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol, TypeAlias
from uuid import UUID

from app.enums.ai_capture_assistant import (
    AdviceConfidence,
    AdviceOutcome,
    AdviceOutputKind,
    AdviceRefusalCode,
    ProviderAdviceStatus,
)
from app.enums.engineering_experience_capture import EngineeringExperienceSourceKind


@dataclass(frozen=True, slots=True)
class CopilotActor:
    actor_id: int
    organization_id: UUID

    def __post_init__(self) -> None:
        if self.actor_id <= 0:
            raise ValueError("actor_id must be positive")


@dataclass(frozen=True, slots=True)
class CopilotScope:
    organization_id: UUID
    project_id: int
    workspace_id: int | None

    def __post_init__(self) -> None:
        if self.project_id <= 0 or (self.workspace_id is not None and self.workspace_id <= 0):
            raise ValueError("scope identifiers must be positive")


@dataclass(frozen=True, slots=True)
class CaptureAdviceRequest:
    capture_id: UUID
    human_instruction: str
    output_kind: AdviceOutputKind = AdviceOutputKind.CAPTURE_REFINEMENT


@dataclass(frozen=True, slots=True)
class AuthorizedCaptureContext:
    capture_id: UUID
    organization_id: UUID
    project_id: int
    workspace_id: int | None
    discipline: str | None
    engineering_object_id: UUID | None
    source_kind: EngineeringExperienceSourceKind
    original_content: str
    source_reference: str | None
    creator_id: int
    lifecycle: Literal["captured"]
    version: int
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class ProviderCaptureAdviceRequest:
    schema_version: Literal[1]
    request_id: UUID
    output_kind: AdviceOutputKind
    human_instruction: str
    context: AuthorizedCaptureContext
    safety_instructions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProviderCaptureAdviceResponseV1:
    status: ProviderAdviceStatus
    suggested_text: str | None
    observations: tuple[str, ...]
    assumptions: tuple[str, ...]
    missing_information: tuple[str, ...]
    confidence: AdviceConfidence
    confidence_rationale: str
    limitations: tuple[str, ...]
    recommended_next_step: str
    refusal_code: AdviceRefusalCode | None
    provider_id: str
    model_id: str
    model_version: str


@dataclass(frozen=True, slots=True)
class CaptureAttribution:
    capture_id: UUID
    version: int
    project_id: int
    workspace_id: int | None
    source_kind: EngineeringExperienceSourceKind
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class ProviderAttribution:
    provider_id: str
    model_id: str
    model_version: str


@dataclass(frozen=True, slots=True)
class CaptureAdviceProposal:
    advisory: Literal[True]
    suggested_text: str
    observations: tuple[str, ...]
    assumptions: tuple[str, ...]
    missing_information: tuple[str, ...]
    confidence: AdviceConfidence
    confidence_rationale: str
    limitations: tuple[str, ...]
    recommended_next_step: str
    capture_attribution: CaptureAttribution
    provider_attribution: ProviderAttribution
    generated_at: datetime


@dataclass(frozen=True, slots=True)
class CaptureAdviceSuccess:
    proposal: CaptureAdviceProposal
    outcome: Literal[AdviceOutcome.SUCCESS] = AdviceOutcome.SUCCESS


@dataclass(frozen=True, slots=True)
class CaptureAdviceRefused:
    refusal_code: AdviceRefusalCode
    recommended_next_step: str
    outcome: Literal[AdviceOutcome.REFUSED] = AdviceOutcome.REFUSED


@dataclass(frozen=True, slots=True)
class CaptureAdviceProtectedNotFound:
    outcome: Literal[AdviceOutcome.PROTECTED_NOT_FOUND] = AdviceOutcome.PROTECTED_NOT_FOUND


@dataclass(frozen=True, slots=True)
class CaptureAdviceInvalidRequest:
    outcome: Literal[AdviceOutcome.INVALID_REQUEST] = AdviceOutcome.INVALID_REQUEST


@dataclass(frozen=True, slots=True)
class CaptureAdviceDisabled:
    outcome: Literal[AdviceOutcome.DISABLED] = AdviceOutcome.DISABLED


@dataclass(frozen=True, slots=True)
class CaptureAdviceUnavailable:
    outcome: Literal[AdviceOutcome.UNAVAILABLE] = AdviceOutcome.UNAVAILABLE


CaptureAdviceResult: TypeAlias = (
    CaptureAdviceSuccess
    | CaptureAdviceRefused
    | CaptureAdviceProtectedNotFound
    | CaptureAdviceInvalidRequest
    | CaptureAdviceDisabled
    | CaptureAdviceUnavailable
)


@dataclass(frozen=True, slots=True)
class CopilotAuditRecord:
    request_id: UUID
    actor_id: int
    action: Literal[
        "AI_CAPTURE_ADVICE_REQUESTED",
        "AI_CAPTURE_ADVICE_COMPLETED",
        "AI_CAPTURE_ADVICE_REFUSED",
        "AI_CAPTURE_ADVICE_FAILED",
    ]
    outcome: str
    instruction_digest: str
    context_digest: str | None
    output_digest: str | None
    provider_id: str | None
    model_id: str | None
    has_workspace_scope: bool


class CaptureAdviceSource(Protocol):
    def read_authorized(self, actor: CopilotActor, capture_id: UUID) -> AuthorizedCaptureContext: ...


class CaptureAdviceProvider(Protocol):
    def propose(self, request: ProviderCaptureAdviceRequest) -> ProviderCaptureAdviceResponseV1: ...


class CopilotAuditRecorder(Protocol):
    def record(self, record: CopilotAuditRecord) -> None: ...


class CopilotClock(Protocol):
    def now(self) -> datetime: ...


class CaptureAdviceApplication(Protocol):
    def advise_capture(
        self, actor: CopilotActor, scope: CopilotScope, request: CaptureAdviceRequest
    ) -> CaptureAdviceResult: ...

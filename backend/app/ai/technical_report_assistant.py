"""Provider-neutral, advisory-only Technical Report assistant adapter."""

from __future__ import annotations

from typing import Protocol

from app.exceptions.technical_report import (
    TechnicalReportAssistantUnavailable,
    TechnicalReportValidationError,
)
from app.ports.technical_report import (
    TechnicalReportAIProposal,
    TechnicalReportAIRequest,
)


class TechnicalReportProposalProvider(Protocol):
    """Provider boundary that has no SATCO authority or persistence access."""

    def propose(self, instruction: str, authorized_context: tuple[str, ...]) -> tuple[str, str]: ...


class ProviderNeutralTechnicalReportAssistant:
    """Translate bounded authorized input into an attributable advisory proposal."""

    def __init__(self, provider: TechnicalReportProposalProvider) -> None:
        self._provider = provider

    def propose(self, request: TechnicalReportAIRequest) -> TechnicalReportAIProposal:
        if not isinstance(request, TechnicalReportAIRequest):
            raise TechnicalReportValidationError("AI request contract is invalid")
        if len(request.authorized_context) < 2:
            raise TechnicalReportValidationError("authorized AI context is required")
        instruction, *context = request.authorized_context
        if not instruction.strip():
            raise TechnicalReportValidationError("Human AI instruction is required")
        try:
            proposal_text, attribution = self._provider.propose(
                instruction, tuple(context)
            )
        except Exception as exc:
            raise TechnicalReportAssistantUnavailable() from exc
        if (
            not isinstance(proposal_text, str)
            or not proposal_text.strip()
            or not isinstance(attribution, str)
            or not attribution.strip()
        ):
            raise TechnicalReportAssistantUnavailable()
        return TechnicalReportAIProposal(
            proposal_text=proposal_text.strip(),
            attribution=attribution.strip(),
        )

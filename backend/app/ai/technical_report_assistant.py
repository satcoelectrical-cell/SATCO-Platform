"""Provider-neutral, advisory-only Technical Report assistant adapter."""

from __future__ import annotations

from typing import Protocol

from app.models.technical_report_command import StandardHistoricalBasisV1, StandardLocator, canonical_json

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


def safe_report_source_context(locator: object) -> str:
    """Return only the safe standards representation permitted before Batch 5."""

    if isinstance(locator, StandardLocator):
        return canonical_json({
            "kind": "legacy_unattested_reference",
            "standard_identity": locator.standard_identity,
            "issuing_authority": locator.issuing_authority,
            "edition": locator.edition,
            "clause_or_location": locator.clause_or_location,
        }).decode("utf-8")
    if isinstance(locator, StandardHistoricalBasisV1):
        return canonical_json({
            "kind": "authorized_standard_basis",
            "basis_id": locator.basis_id,
            "materiality": locator.materiality,
            "issuer": locator.issuer,
            "designation": locator.designation,
            "title": locator.title,
            "edition_designation": locator.edition_designation,
            "standing": locator.standing,
            "basis_digest": locator.basis_digest,
        }).decode("utf-8")
    return canonical_json(locator).decode("utf-8")

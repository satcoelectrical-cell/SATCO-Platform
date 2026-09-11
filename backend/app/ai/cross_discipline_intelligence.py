"""Bounded optional advisory generation for PATCH-053 Batch-5."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class CrossDisciplineAIProvider(Protocol):
    def complete(self, prompt: str) -> str: ...


@dataclass(frozen=True, slots=True)
class AdvisoryExplanation:
    summary: str
    draft_next_actions: tuple[str, ...]
    advisory: bool = True


class BoundedCrossDisciplineAI:
    """One provider call, no retry, no side effects and no authority mutation."""

    def __init__(self, provider: CrossDisciplineAIProvider | None = None, *, enabled: bool = False):
        self.provider = provider
        self.enabled = enabled

    def explain(self, findings: tuple[dict, ...]) -> AdvisoryExplanation | None:
        if not self.enabled or self.provider is None:
            return None
        if not 1 <= len(findings) <= 20:
            raise ValueError("invalid_request")
        prompt = "\n".join(
            f"- {item.get('category', '')}: {item.get('subcode', '')}" for item in findings
        )
        if len(prompt.encode("utf-8")) > 65_536:
            raise ValueError("invalid_request")
        try:
            response = self.provider.complete(prompt)
        except Exception:
            return None
        if not isinstance(response, str) or len(response.encode("utf-8")) > 65_536:
            return None
        return AdvisoryExplanation(response, ())

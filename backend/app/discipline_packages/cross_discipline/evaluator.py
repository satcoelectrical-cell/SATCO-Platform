"""Deterministic generic evaluation pipeline without production pair rules."""

from __future__ import annotations

from uuid import uuid4

from .canonical import digest, finding_fingerprint, recurrence_key
from .contracts import (
    EvaluationInputV1, EvaluationResultV1, FindingV1, LIMITS,
    RuleIndeterminate, enforce_resource_limit,
)


SEVERITY_RANK = {"critical": 0, "major": 1, "warning": 2, "info": 3}


class EvaluationInvariantError(ValueError):
    pass


class GenericEvaluator:
    def __init__(self, handlers=None):
        self._handlers = dict(handlers or {})

    @property
    def registered_rule_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))

    def evaluate(self, request: EvaluationInputV1) -> EvaluationResultV1:
        try:
            enforce_resource_limit("rules", len(request.values_by_rule))
        except ValueError:
            return self._terminal("indeterminate", "resource_limit_exceeded")
        findings = []
        for rule_id in sorted(request.values_by_rule):
            handler = self._handlers.get(rule_id)
            if handler is None:
                return self._terminal("unavailable", "artifact_unavailable")
            try:
                produced = tuple(handler(request, request.values_by_rule[rule_id]))
            except RuleIndeterminate as error:
                # A required operand that cannot be proven makes the entire
                # assessment closed/indeterminate.  Do not retain Findings
                # produced by rules evaluated earlier in this run.
                return self._terminal("indeterminate", error.reason_code)
            try:
                enforce_resource_limit("findings_per_rule", len(produced))
            except ValueError:
                return self._terminal("indeterminate", "resource_limit_exceeded")
            for identity, severity, comparison_outcome in produced:
                fingerprint = finding_fingerprint(identity)
                recurrence = recurrence_key(identity)
                sort_key = (
                    SEVERITY_RANK[severity], identity.category, identity.subcode,
                    identity.occurrence_key, identity.affected_selector, fingerprint,
                )
                findings.append(FindingV1(
                    str(uuid4()), identity, severity, comparison_outcome,
                    fingerprint, recurrence, sort_key,
                ))
        try:
            enforce_resource_limit("findings", len(findings))
        except ValueError:
            return self._terminal("indeterminate", "resource_limit_exceeded")
        if len({item.fingerprint for item in findings}) != len(findings):
            raise EvaluationInvariantError("duplicate Finding fingerprint")
        ordered = tuple(sorted(findings, key=lambda item: item.sort_key))
        finding_set_digest = digest(ordered, "satco:cross-discipline-finding-set:v1")
        status = "completed_with_findings" if ordered else "completed_no_findings"
        result_digest = digest(
            {"status": status, "finding_set_digest": finding_set_digest},
            "satco:cross-discipline-result:v1",
        )
        return EvaluationResultV1(status, None, ordered, finding_set_digest, result_digest)

    @staticmethod
    def _terminal(status: str, reason: str) -> EvaluationResultV1:
        empty = digest((), "satco:cross-discipline-finding-set:v1")
        result = digest(
            {"status": status, "reason_code": reason, "finding_set_digest": empty},
            "satco:cross-discipline-result:v1",
        )
        return EvaluationResultV1(status, reason, (), empty, result)


def batch_two_evaluator() -> GenericEvaluator:
    """Explicit Batch-2 registration; Batch-1 callers retain the empty evaluator."""
    from .rules.eic_v1 import BATCH_TWO_RULE_HANDLERS
    return GenericEvaluator(BATCH_TWO_RULE_HANDLERS)


def batch_three_evaluator() -> GenericEvaluator:
    """Explicit Batch-3 I↔C registration; retained Batch-1/2 evaluators remain frozen."""
    from .rules.eic_v1 import BATCH_THREE_RULE_HANDLERS
    return GenericEvaluator(BATCH_THREE_RULE_HANDLERS)


def batch_four_evaluator() -> GenericEvaluator:
    """Explicit Batch-4 Electrical ↔ C&A registration."""
    from .rules.eic_v1 import BATCH_FOUR_RULE_HANDLERS
    return GenericEvaluator(BATCH_FOUR_RULE_HANDLERS)


def batch_five_evaluator() -> GenericEvaluator:
    """Explicit Batch-5 registration for the bounded E+I+C change path."""
    from .rules.eic_v1 import BATCH_FIVE_RULE_HANDLERS
    return GenericEvaluator(BATCH_FIVE_RULE_HANDLERS)
